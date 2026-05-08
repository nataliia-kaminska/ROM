from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import ensure_profile_access, get_optional_current_user
from app.db.session import get_db
from app.repositories import opportunities as opportunity_repository
from app.repositories import profiles as profile_repository
from app.repositories import workflow as workflow_repository
from app.schemas.reminders import OpportunityReminderCreate, OpportunityReminderRead
from app.services.reminders import complete_reminder, create_reminder


router = APIRouter(prefix="/profiles/{profile_id}/reminders", tags=["reminders"])


@router.post("", response_model=OpportunityReminderRead, status_code=status.HTTP_201_CREATED)
def create_profile_reminder(
    profile_id: int,
    payload: OpportunityReminderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> OpportunityReminderRead:
    ensure_profile_access(profile_repository.get_profile(db, profile_id), current_user)
    opportunity = opportunity_repository.get_opportunity(db, payload.opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    reminder = create_reminder(
        db=db,
        profile_id=profile_id,
        opportunity=opportunity,
        remind_on=payload.remind_on,
        message=payload.message,
    )
    db.commit()
    db.refresh(reminder)
    return reminder


@router.get("", response_model=list[OpportunityReminderRead])
def list_profile_reminders(
    profile_id: int,
    due_only: bool = False,
    include_completed: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> list[OpportunityReminderRead]:
    ensure_profile_access(profile_repository.get_profile(db, profile_id), current_user)
    return workflow_repository.list_profile_reminders(
        db,
        profile_id=profile_id,
        include_completed=include_completed,
        due_only=due_only,
    )


@router.put("/{reminder_id}/complete", response_model=OpportunityReminderRead)
def complete_profile_reminder(
    profile_id: int,
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
) -> OpportunityReminderRead:
    ensure_profile_access(profile_repository.get_profile(db, profile_id), current_user)
    reminder = workflow_repository.get_profile_reminder(db, profile_id, reminder_id)
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")

    complete_reminder(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder
