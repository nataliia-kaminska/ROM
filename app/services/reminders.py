from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models import Opportunity, OpportunityReminder, ReminderStatus


def create_reminder(
    db: Session,
    profile_id: int,
    opportunity: Opportunity,
    remind_on: date,
    message: str = "",
) -> OpportunityReminder:
    existing = (
        db.query(OpportunityReminder)
        .filter(
            OpportunityReminder.profile_id == profile_id,
            OpportunityReminder.opportunity_id == opportunity.id,
            OpportunityReminder.remind_on == remind_on,
        )
        .first()
    )
    if existing:
        if message:
            existing.message = message
        return existing

    reminder = OpportunityReminder(
        profile_id=profile_id,
        opportunity_id=opportunity.id,
        remind_on=remind_on,
        message=message or _default_message(opportunity),
    )
    db.add(reminder)
    return reminder


def ensure_deadline_reminder(db: Session, profile_id: int, opportunity: Opportunity) -> OpportunityReminder | None:
    if opportunity.deadline is None:
        return None

    today = date.today()
    remind_on = max(today, opportunity.deadline - timedelta(days=7))
    if opportunity.deadline < today:
        return None

    return create_reminder(
        db=db,
        profile_id=profile_id,
        opportunity=opportunity,
        remind_on=remind_on,
        message=_default_message(opportunity),
    )


def complete_reminder(reminder: OpportunityReminder) -> OpportunityReminder:
    reminder.status = ReminderStatus.completed
    reminder.completed_at = datetime.utcnow()
    return reminder


def _default_message(opportunity: Opportunity) -> str:
    if opportunity.deadline:
        return f"Deadline for {opportunity.title} is {opportunity.deadline.isoformat()}"
    return f"Review {opportunity.title}"

