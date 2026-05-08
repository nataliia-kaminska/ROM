from datetime import date

from sqlalchemy.orm import Session

from app.db.models import OpportunityReminder, ProfileOpportunityStatus, ReminderStatus


def get_profile_opportunity_status(
    db: Session,
    profile_id: int,
    opportunity_id: int,
) -> ProfileOpportunityStatus | None:
    return (
        db.query(ProfileOpportunityStatus)
        .filter(
            ProfileOpportunityStatus.profile_id == profile_id,
            ProfileOpportunityStatus.opportunity_id == opportunity_id,
        )
        .first()
    )


def list_profile_statuses(db: Session, profile_id: int) -> list[ProfileOpportunityStatus]:
    return db.query(ProfileOpportunityStatus).filter(ProfileOpportunityStatus.profile_id == profile_id).all()


def list_profile_statuses_recent(db: Session, profile_id: int) -> list[ProfileOpportunityStatus]:
    return (
        db.query(ProfileOpportunityStatus)
        .filter(ProfileOpportunityStatus.profile_id == profile_id)
        .order_by(ProfileOpportunityStatus.updated_at.desc())
        .all()
    )


def get_reminder(db: Session, reminder_id: int) -> OpportunityReminder | None:
    return db.get(OpportunityReminder, reminder_id)


def get_profile_reminder(db: Session, profile_id: int, reminder_id: int) -> OpportunityReminder | None:
    return (
        db.query(OpportunityReminder)
        .filter(
            OpportunityReminder.profile_id == profile_id,
            OpportunityReminder.id == reminder_id,
        )
        .first()
    )


def list_profile_reminders(
    db: Session,
    profile_id: int,
    include_completed: bool = False,
    due_only: bool = False,
) -> list[OpportunityReminder]:
    query = db.query(OpportunityReminder).filter(OpportunityReminder.profile_id == profile_id)
    if not include_completed:
        query = query.filter(OpportunityReminder.status == ReminderStatus.pending)
    if due_only:
        query = query.filter(OpportunityReminder.remind_on <= date.today())
    return query.order_by(OpportunityReminder.remind_on.asc()).all()


def list_due_reminders(db: Session, scan_date: date) -> list[OpportunityReminder]:
    return (
        db.query(OpportunityReminder)
        .filter(
            OpportunityReminder.status == ReminderStatus.pending,
            OpportunityReminder.remind_on <= scan_date,
        )
        .order_by(OpportunityReminder.remind_on.asc())
        .all()
    )
