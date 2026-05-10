from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Opportunity, ProfileOpportunityStatusValue, ResearcherProfile, ResearcherProfileDetails
from app.modules.opportunities.mappers import to_opportunity_read
from app.repositories import profiles as profile_repository
from app.repositories import workflow as workflow_repository
from app.schemas.recommendations import RecommendationRead
from app.services.embeddings import persist_profile_embedding_vector, ensure_profile_embedding, vector_literal
from app.services.recommendation_engine import build_history_signals, score_opportunity
from app.services.requirements import build_gap_analysis


@dataclass(frozen=True)
class RecommendationQuery:
    include_ignored: bool = False
    min_score: int = 0
    limit: int = 50
    offset: int = 0


class CandidateSelector(Protocol):
    def select(
        self,
        db: Session,
        profile: ResearcherProfile,
        details: ResearcherProfileDetails | None,
    ) -> list[Opportunity]:
        ...


class SqliteAllCandidateSelector:
    def select(
        self,
        db: Session,
        profile: ResearcherProfile,
        details: ResearcherProfileDetails | None,
    ) -> list[Opportunity]:
        return db.query(Opportunity).all()


class PostgresVectorCandidateSelector:
    def select(
        self,
        db: Session,
        profile: ResearcherProfile,
        details: ResearcherProfileDetails | None,
    ) -> list[Opportunity]:
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
            return SqliteAllCandidateSelector().select(db, profile, details)
        return db.query(Opportunity).filter(Opportunity.id.in_(candidate_ids)).all()


def get_candidate_selector(db: Session) -> CandidateSelector:
    if db.bind and db.bind.dialect.name == "postgresql":
        return PostgresVectorCandidateSelector()
    return SqliteAllCandidateSelector()


def list_recommendations(
    db: Session,
    profile: ResearcherProfile,
    query: RecommendationQuery,
    selector: CandidateSelector | None = None,
) -> list[RecommendationRead]:
    details = profile_repository.get_profile_details(db, profile.id)
    status_records = workflow_repository.list_profile_statuses(db, profile.id)
    statuses_by_opportunity_id = {record.opportunity_id: record for record in status_records}

    opportunities = (selector or get_candidate_selector(db)).select(db, profile, details)
    opportunities_by_id = {opportunity.id: opportunity for opportunity in opportunities}
    history_signals = build_history_signals(status_records, opportunities_by_id)
    recommendations = []
    for opportunity in opportunities:
        status_record = statuses_by_opportunity_id.get(opportunity.id)
        if (
            not query.include_ignored
            and status_record
            and status_record.status == ProfileOpportunityStatusValue.ignored
        ):
            continue

        scored = score_opportunity(profile, opportunity, details, status_record, history_signals)
        if scored.final_score < query.min_score:
            continue

        gaps = build_gap_analysis(profile, opportunity, details)
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
    sorted_recommendations = sorted(recommendations, key=lambda item: item.match_score, reverse=True)
    return sorted_recommendations[query.offset : query.offset + query.limit]
