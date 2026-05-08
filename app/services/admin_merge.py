from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models import (
    Notification,
    Opportunity,
    OpportunityReminder,
    ProfileOpportunityStatus,
    ProfileOpportunityStatusValue,
    ReminderStatus,
)
from app.services.admin_ops import log_admin_action


def merge_duplicate_opportunities(
    db: Session,
    target_opportunity_id: int,
    duplicate_opportunity_ids: list[int],
    actor_user_id: int | None,
) -> Opportunity:
    target = db.get(Opportunity, target_opportunity_id)
    if target is None:
        raise NotFoundError("Target opportunity not found")

    duplicates_to_remove = db.query(Opportunity).filter(Opportunity.id.in_(duplicate_opportunity_ids)).all()
    for duplicate in duplicates_to_remove:
        if duplicate.id == target.id:
            continue
        _merge_status_records(db, duplicate.id, target.id)
        _merge_reminder_records(db, duplicate.id, target.id)
        db.query(Notification).filter(Notification.opportunity_id == duplicate.id).update(
            {Notification.opportunity_id: target.id}
        )
        db.delete(duplicate)

    log_admin_action(
        db,
        actor_user_id,
        "merge",
        "opportunity",
        target.id,
        f"Merged duplicates: {duplicate_opportunity_ids}",
    )
    db.commit()
    db.refresh(target)
    return target


def _merge_status_records(db: Session, duplicate_id: int, target_id: int) -> None:
    duplicate_records = db.query(ProfileOpportunityStatus).filter(ProfileOpportunityStatus.opportunity_id == duplicate_id).all()
    for duplicate_record in duplicate_records:
        target_record = (
            db.query(ProfileOpportunityStatus)
            .filter(
                ProfileOpportunityStatus.profile_id == duplicate_record.profile_id,
                ProfileOpportunityStatus.opportunity_id == target_id,
            )
            .first()
        )
        if target_record is None:
            duplicate_record.opportunity_id = target_id
            continue
        target_record.status = _preferred_status(target_record.status, duplicate_record.status)
        target_record.notes = _combine_notes(target_record.notes, duplicate_record.notes)
        db.delete(duplicate_record)
    db.flush()


def _merge_reminder_records(db: Session, duplicate_id: int, target_id: int) -> None:
    duplicate_records = db.query(OpportunityReminder).filter(OpportunityReminder.opportunity_id == duplicate_id).all()
    for duplicate_record in duplicate_records:
        target_record = (
            db.query(OpportunityReminder)
            .filter(
                OpportunityReminder.profile_id == duplicate_record.profile_id,
                OpportunityReminder.opportunity_id == target_id,
                OpportunityReminder.remind_on == duplicate_record.remind_on,
            )
            .first()
        )
        if target_record is None:
            duplicate_record.opportunity_id = target_id
            continue
        if duplicate_record.status == ReminderStatus.pending:
            target_record.status = ReminderStatus.pending
            target_record.completed_at = None
        elif target_record.completed_at is None:
            target_record.completed_at = duplicate_record.completed_at
        target_record.message = _combine_notes(target_record.message, duplicate_record.message)
        db.delete(duplicate_record)
    db.flush()


def _preferred_status(
    first: ProfileOpportunityStatusValue,
    second: ProfileOpportunityStatusValue,
) -> ProfileOpportunityStatusValue:
    rank = {
        ProfileOpportunityStatusValue.accepted: 6,
        ProfileOpportunityStatusValue.applied: 5,
        ProfileOpportunityStatusValue.planned: 4,
        ProfileOpportunityStatusValue.saved: 3,
        ProfileOpportunityStatusValue.rejected: 2,
        ProfileOpportunityStatusValue.ignored: 1,
    }
    return first if rank[first] >= rank[second] else second


def _combine_notes(first: str, second: str) -> str:
    values = []
    for value in (first, second):
        cleaned = value.strip()
        if cleaned and cleaned not in values:
            values.append(cleaned)
    return "\n".join(values)
