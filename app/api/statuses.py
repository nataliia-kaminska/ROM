from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import ensure_profile_access, get_optional_current_user
from app.db.models import Opportunity, ProfileOpportunityStatus, ProfileOpportunityStatusValue, ResearcherProfile
from app.db.session import get_db
from app.schemas.statuses import ProfileOpportunityStatusCreate, ProfileOpportunityStatusRead
from app.services.reminders import ensure_deadline_reminder


router = APIRouter(prefix="/profiles/{profile_id}/opportunities", tags=["profile opportunity statuses"])


@router.put(
    "/{opportunity_id}/status",
    response_model=ProfileOpportunityStatusRead,
    status_code=status.HTTP_200_OK,
)
def upsert_opportunity_status(
    profile_id: int,
    opportunity_id: int,
    payload: ProfileOpportunityStatusCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> ProfileOpportunityStatusRead:
    ensure_profile_access(db.get(ResearcherProfile, profile_id), current_user)
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    existing = (
        db.query(ProfileOpportunityStatus)
        .filter(
            ProfileOpportunityStatus.profile_id == profile_id,
            ProfileOpportunityStatus.opportunity_id == opportunity_id,
        )
        .first()
    )
    if existing:
        existing.status = payload.status
        existing.notes = payload.notes
        record = existing
    else:
        record = ProfileOpportunityStatus(
            profile_id=profile_id,
            opportunity_id=opportunity_id,
            status=payload.status,
            notes=payload.notes,
        )
        db.add(record)

    if payload.status in {
        ProfileOpportunityStatusValue.saved,
        ProfileOpportunityStatusValue.planned,
        ProfileOpportunityStatusValue.applied,
    }:
        ensure_deadline_reminder(db, profile_id, opportunity)

    db.commit()
    db.refresh(record)
    return record


@router.get("/statuses", response_model=list[ProfileOpportunityStatusRead])
def list_opportunity_statuses(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> list[ProfileOpportunityStatusRead]:
    ensure_profile_access(db.get(ResearcherProfile, profile_id), current_user)
    return (
        db.query(ProfileOpportunityStatus)
        .filter(ProfileOpportunityStatus.profile_id == profile_id)
        .order_by(ProfileOpportunityStatus.updated_at.desc())
        .all()
    )
