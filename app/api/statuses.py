from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import ensure_profile_access, get_optional_current_user
from app.db.models import ProfileOpportunityStatus, ProfileOpportunityStatusValue
from app.db.session import get_db
from app.repositories import opportunities as opportunity_repository
from app.repositories import profiles as profile_repository
from app.repositories import workflow as workflow_repository
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
    ensure_profile_access(profile_repository.get_profile(db, profile_id), current_user)
    opportunity = opportunity_repository.get_opportunity(db, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    existing = workflow_repository.get_profile_opportunity_status(db, profile_id, opportunity_id)
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
    ensure_profile_access(profile_repository.get_profile(db, profile_id), current_user)
    return workflow_repository.list_profile_statuses_recent(db, profile_id)
