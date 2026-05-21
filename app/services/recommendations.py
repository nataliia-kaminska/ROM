from dataclasses import dataclass
from datetime import date, datetime
import logging
from time import perf_counter
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Opportunity, ProfileOpportunityStatusValue, ResearcherProfile, ResearcherProfileDetails
from app.modules.opportunities.mappers import to_opportunity_read
from app.repositories import opportunities as opportunity_repository
from app.repositories import profiles as profile_repository
from app.repositories import workflow as workflow_repository
from app.schemas.recommendations import RecommendationRead
from app.services.embeddings import persist_profile_embedding_vector, ensure_profile_embedding, vector_literal
from app.services.recommendation_engine import build_history_signals, score_opportunity
from app.services.requirements import build_gap_analysis

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecommendationQuery:
    include_ignored: bool = False
    min_score: int = 0
    limit: int = 50
    offset: int = 0
    keyword: str | None = None
    source: str | None = None
    opportunity_type: str | None = None
    country: str | None = None
    career_stage: str | None = None
    active_only: bool = True
    sort_by: str = "match_score"
    sort_order: str = "desc"
    exact_total: bool = False


@dataclass(frozen=True)
class RecommendationPage:
    items: list[RecommendationRead]
    total: int


class CandidateSelector(Protocol):
    def select(
        self,
        db: Session,
        profile: ResearcherProfile,
        details: ResearcherProfileDetails | None,
        query: RecommendationQuery,
    ) -> list[Opportunity]:
        ...


class SqliteAllCandidateSelector:
    def select(
        self,
        db: Session,
        profile: ResearcherProfile,
        details: ResearcherProfileDetails | None,
        query: RecommendationQuery,
    ) -> list[Opportunity]:
        candidate_limit = (
            max(settings.semantic_candidate_limit, query.offset + query.limit)
            if query.exact_total
            else max(query.offset + query.limit, min(settings.semantic_candidate_limit, query.offset + max(query.limit * 3, 60)))
        )
        return opportunity_repository.list_opportunities(
            db,
            source=query.source,
            opportunity_type=query.opportunity_type,
            country=query.country,
            career_stage=query.career_stage,
            keyword=query.keyword,
            active_only=query.active_only,
            sort_by=_catalog_sort_by(query.sort_by),
            sort_order=query.sort_order,
            limit=candidate_limit,
            offset=0,
        )


class PostgresVectorCandidateSelector:
    def select(
        self,
        db: Session,
        profile: ResearcherProfile,
        details: ResearcherProfileDetails | None,
        query: RecommendationQuery,
    ) -> list[Opportunity]:
        if _has_catalog_filters(query):
            return SqliteAllCandidateSelector().select(db, profile, details, query)
        if details is not None:
            persist_profile_embedding_vector(db, profile, details)
        profile_vector = ensure_profile_embedding(profile, details)
        candidate_rows = db.execute(
            text(
                """
                SELECT id
                FROM opportunities
                WHERE opportunity_embedding_vector IS NOT NULL
                ORDER BY opportunity_embedding_vector <=> CAST(:profile_vector AS vector)
                LIMIT :limit
                """
            ),
            {"profile_vector": vector_literal(profile_vector), "limit": settings.semantic_candidate_limit},
        ).all()
        candidate_ids = [row[0] for row in candidate_rows]
        if not candidate_ids:
            return SqliteAllCandidateSelector().select(db, profile, details, query)
        return db.query(Opportunity).filter(Opportunity.id.in_(candidate_ids)).all()


def get_candidate_selector(db: Session) -> CandidateSelector:
    if db.bind and db.bind.dialect.name == "postgresql":
        return PostgresVectorCandidateSelector()
    return SqliteAllCandidateSelector()


def _has_catalog_filters(query: RecommendationQuery) -> bool:
    return any(
        [
            query.keyword,
            query.source,
            query.opportunity_type,
            query.country,
            query.career_stage,
            not query.active_only,
        ]
    )


def list_recommendations(
    db: Session,
    profile: ResearcherProfile,
    query: RecommendationQuery,
    selector: CandidateSelector | None = None,
) -> list[RecommendationRead]:
    fast_query = RecommendationQuery(**{**query.__dict__, "exact_total": False})
    return list_recommendations_page(db, profile, fast_query, selector).items


def list_recommendations_page(
    db: Session,
    profile: ResearcherProfile,
    query: RecommendationQuery,
    selector: CandidateSelector | None = None,
) -> RecommendationPage:
    started_at = perf_counter()
    logger.info(
        "recommendations start profile_id=%s min_score=%s include_ignored=%s limit=%s offset=%s",
        profile.id,
        query.min_score,
        query.include_ignored,
        query.limit,
        query.offset,
    )
    details = profile_repository.get_profile_details(db, profile.id)
    status_records = workflow_repository.list_profile_statuses(db, profile.id)
    statuses_by_opportunity_id = {record.opportunity_id: record for record in status_records}

    profile_vector_started_at = perf_counter()
    profile_vector = ensure_profile_embedding(profile, details)
    logger.info(
        "recommendations profile embedding ready profile_id=%s dimensions=%s duration_ms=%.2f",
        profile.id,
        len(profile_vector),
        (perf_counter() - profile_vector_started_at) * 1000,
    )

    selector_instance = selector or get_candidate_selector(db)
    selection_started_at = perf_counter()
    opportunities = selector_instance.select(db, profile, details, query)
    logger.info(
        "recommendations candidates selected profile_id=%s selector=%s candidates=%s duration_ms=%.2f",
        profile.id,
        selector_instance.__class__.__name__,
        len(opportunities),
        (perf_counter() - selection_started_at) * 1000,
    )
    opportunities_by_id = {opportunity.id: opportunity for opportunity in opportunities}
    history_signals = build_history_signals(status_records, opportunities_by_id)
    recommendations = []
    missing_embedding_count = 0
    scoring_started_at = perf_counter()
    for opportunity in opportunities:
        item_started_at = perf_counter()
        status_record = statuses_by_opportunity_id.get(opportunity.id)
        if (
            not query.include_ignored
            and status_record
            and status_record.status == ProfileOpportunityStatusValue.ignored
        ):
            continue

        scored = score_opportunity(profile, opportunity, details, status_record, history_signals, profile_vector)
        if scored.breakdown.semantic == 0 and not opportunity.opportunity_embedding:
            missing_embedding_count += 1
        if scored.final_score < query.min_score:
            continue

        gaps = build_gap_analysis(profile, opportunity, details)
        item_duration_ms = (perf_counter() - item_started_at) * 1000
        if item_duration_ms >= 100:
            logger.info(
                "recommendations slow candidate profile_id=%s opportunity_id=%s score=%s duration_ms=%.2f",
                profile.id,
                opportunity.id,
                scored.final_score,
                item_duration_ms,
            )
        recommendations.append(
            RecommendationRead(
                opportunity=to_opportunity_read(opportunity),
                match_score=scored.final_score,
                semantic_score=scored.breakdown.semantic,
                score_breakdown=scored.breakdown,
                reasons=scored.reasons,
                readiness_score=gaps.readiness_score,
                gaps=gaps.gaps,
                strengths=gaps.strengths,
                user_status=status_record.status.value if status_record else None,
            )
        )

    db.commit()
    sorted_recommendations = _sort_recommendations(recommendations, query.sort_by, query.sort_order)
    page = sorted_recommendations[query.offset : query.offset + query.limit]
    logger.info(
        "recommendations complete profile_id=%s candidates=%s scored=%s returned=%s scoring_ms=%.2f total_ms=%.2f",
        profile.id,
        len(opportunities),
        len(recommendations),
        len(page),
        (perf_counter() - scoring_started_at) * 1000,
        (perf_counter() - started_at) * 1000,
    )
    if missing_embedding_count:
        logger.info(
            "recommendations used eligibility/history fallback for opportunities without embeddings profile_id=%s missing_embeddings=%s",
            profile.id,
            missing_embedding_count,
        )
    return RecommendationPage(items=page, total=len(sorted_recommendations))


def _sort_recommendations(recommendations: list[RecommendationRead], sort_by: str, sort_order: str) -> list[RecommendationRead]:
    reverse = sort_order == "desc"
    if sort_by == "deadline":
        return sorted(recommendations, key=lambda item: (item.opportunity.deadline is None, item.opportunity.deadline or date.max), reverse=reverse)
    if sort_by == "created_at":
        return sorted(recommendations, key=lambda item: item.opportunity.created_at or datetime.min, reverse=reverse)
    if sort_by == "title":
        return sorted(recommendations, key=lambda item: item.opportunity.title.casefold(), reverse=reverse)
    if sort_by == "source":
        return sorted(recommendations, key=lambda item: (item.opportunity.source.casefold(), item.opportunity.title.casefold()), reverse=reverse)
    if sort_by == "readiness_score":
        return sorted(recommendations, key=lambda item: item.readiness_score, reverse=reverse)
    if sort_by == "semantic_score":
        return sorted(recommendations, key=lambda item: item.semantic_score, reverse=reverse)
    return sorted(recommendations, key=lambda item: item.match_score, reverse=reverse)


def _catalog_sort_by(sort_by: str) -> str:
    return sort_by if sort_by in {"deadline", "created_at", "title", "source"} else "deadline"
