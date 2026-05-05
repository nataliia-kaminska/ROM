from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.api.opportunities import _to_read
from app.db.models import (
    AdminAuditLog,
    IngestionBatch,
    IngestionBatchStatus,
    Notification,
    Opportunity,
    OpportunityReminder,
    OpportunitySource,
    ProfileOpportunityStatus,
    ProfileOpportunityStatusValue,
    ReminderStatus,
)
from app.db.session import get_db
from app.schemas.admin import AdminAnalyticsRead, AdminAuditLogRead, AdminDashboardRead, DuplicateMergeRequest, DuplicateOpportunityGroup
from app.schemas.opportunities import OpportunityCreate, OpportunityRead
from app.services.admin_ops import build_admin_analytics, duplicate_groups, log_admin_action
from app.services.opportunity_import import apply_opportunity_payload


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/dashboard", response_model=AdminDashboardRead)
def dashboard(db: Session = Depends(get_db)) -> AdminDashboardRead:
    return AdminDashboardRead(
        sources=db.query(OpportunitySource).order_by(OpportunitySource.name.asc()).all(),
        recent_batches=db.query(IngestionBatch).order_by(IngestionBatch.started_at.desc()).limit(10).all(),
        failed_batches=(
            db.query(IngestionBatch)
            .filter(IngestionBatch.status == IngestionBatchStatus.failed)
            .order_by(IngestionBatch.started_at.desc())
            .limit(10)
            .all()
        ),
        analytics=build_admin_analytics(db),
    )


@router.get("/analytics", response_model=AdminAnalyticsRead)
def analytics(db: Session = Depends(get_db)) -> AdminAnalyticsRead:
    return build_admin_analytics(db)


@router.get("/audit-log", response_model=list[AdminAuditLogRead])
def audit_log(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[AdminAuditLogRead]:
    return db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/opportunities/duplicates", response_model=list[DuplicateOpportunityGroup])
def duplicates(db: Session = Depends(get_db)) -> list[DuplicateOpportunityGroup]:
    return [
        DuplicateOpportunityGroup(key=f"group-{index + 1}", opportunities=[_to_read(item) for item in group])
        for index, group in enumerate(duplicate_groups(db))
    ]


@router.post("/opportunities/merge", response_model=OpportunityRead)
def merge_duplicates(
    payload: DuplicateMergeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
) -> OpportunityRead:
    target = db.get(Opportunity, payload.target_opportunity_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Target opportunity not found")
    duplicates_to_remove = db.query(Opportunity).filter(Opportunity.id.in_(payload.duplicate_opportunity_ids)).all()
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
        current_user.id if current_user else None,
        "merge",
        "opportunity",
        target.id,
        f"Merged duplicates: {payload.duplicate_opportunity_ids}",
    )
    db.commit()
    db.refresh(target)
    return _to_read(target)


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


@router.put("/opportunities/{opportunity_id}", response_model=OpportunityRead)
def edit_opportunity(
    opportunity_id: int,
    payload: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
) -> OpportunityRead:
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    apply_opportunity_payload(opportunity, payload)
    opportunity.opportunity_embedding = ""
    log_admin_action(db, current_user.id if current_user else None, "edit", "opportunity", opportunity_id, f"Edited {payload.title}")
    db.commit()
    db.refresh(opportunity)
    return _to_read(opportunity)
