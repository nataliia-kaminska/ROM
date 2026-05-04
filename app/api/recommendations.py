from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import ensure_profile_access, get_optional_current_user
from app.api.opportunities import _to_read
from app.db.models import Opportunity, ProfileOpportunityStatus, ProfileOpportunityStatusValue, ResearcherProfile, ResearcherProfileDetails
from app.db.session import get_db
from app.schemas.recommendations import RecommendationRead
from app.services.recommendation_engine import score_opportunity


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

    opportunities = db.query(Opportunity).all()
    recommendations = []
    for opportunity in opportunities:
        status_record = statuses_by_opportunity_id.get(opportunity.id)
        if (
            not include_ignored
            and status_record
            and status_record.status == ProfileOpportunityStatusValue.ignored
        ):
            continue

        match_score, reasons, semantic_score = score_opportunity(profile, opportunity, details, status_record)
        if match_score >= min_score:
            recommendations.append(
                RecommendationRead(
                    opportunity=_to_read(opportunity),
                    match_score=match_score,
                    semantic_score=semantic_score,
                    reasons=reasons,
                    user_status=status_record.status.value if status_record else None,
                )
            )

    db.commit()
    return sorted(recommendations, key=lambda item: item.match_score, reverse=True)[offset : offset + limit]
