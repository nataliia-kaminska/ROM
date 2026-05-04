from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.dependencies import ensure_profile_access, get_optional_current_user
from app.api.opportunities import _to_read
from app.core.config import settings
from app.db.models import Opportunity, ProfileOpportunityStatus, ProfileOpportunityStatusValue, ResearcherProfile, ResearcherProfileDetails
from app.db.session import get_db
from app.schemas.recommendations import RecommendationRead
from app.services.embeddings import ensure_profile_embedding, vector_literal
from app.services.recommendation_engine import build_history_signals, score_opportunity
from app.services.requirements import build_gap_analysis


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/{profile_id}", response_model=list[RecommendationRead])
def get_recommendations(
    profile_id: int,
    include_ignored: bool = False,
    min_score: int = Query(default=0, ge=0, le=100),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> list[RecommendationRead]:
    profile = ensure_profile_access(db.get(ResearcherProfile, profile_id), current_user)

    details = db.query(ResearcherProfileDetails).filter(ResearcherProfileDetails.profile_id == profile_id).first()
    status_records = (
        db.query(ProfileOpportunityStatus).filter(ProfileOpportunityStatus.profile_id == profile_id).all()
    )
    statuses_by_opportunity_id = {record.opportunity_id: record for record in status_records}

    opportunities = _candidate_opportunities(db, profile, details)
    opportunities_by_id = {opportunity.id: opportunity for opportunity in opportunities}
    history_signals = build_history_signals(status_records, opportunities_by_id)
    recommendations = []
    for opportunity in opportunities:
        status_record = statuses_by_opportunity_id.get(opportunity.id)
        if (
            not include_ignored
            and status_record
            and status_record.status == ProfileOpportunityStatusValue.ignored
        ):
            continue

        scored = score_opportunity(profile, opportunity, details, status_record, history_signals)
        gaps = build_gap_analysis(profile, opportunity, details)
        if scored.final_score >= min_score:
            recommendations.append(
                RecommendationRead(
                    opportunity=_to_read(opportunity),
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
    return sorted(recommendations, key=lambda item: item.match_score, reverse=True)[offset : offset + limit]


def _candidate_opportunities(
    db: Session,
    profile: ResearcherProfile,
    details: ResearcherProfileDetails | None,
) -> list[Opportunity]:
    if db.bind and db.bind.dialect.name == "postgresql":
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
        if candidate_ids:
            return db.query(Opportunity).filter(Opportunity.id.in_(candidate_ids)).all()
    return db.query(Opportunity).all()
