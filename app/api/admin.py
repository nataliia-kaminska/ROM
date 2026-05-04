from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_optional_current_user
from app.api.opportunities import _to_read
from app.db.models import AdminAuditLog, IngestionBatch, IngestionBatchStatus, Notification, Opportunity, OpportunityReminder, OpportunitySource, ProfileOpportunityStatus
from app.db.session import get_db
from app.schemas.admin import AdminAnalyticsRead, AdminAuditLogRead, AdminDashboardRead, DuplicateMergeRequest, DuplicateOpportunityGroup
from app.schemas.opportunities import OpportunityCreate, OpportunityRead
from app.services.admin_ops import build_admin_analytics, duplicate_groups, log_admin_action
from app.services.opportunity_import import apply_opportunity_payload


router = APIRouter(prefix="/admin", tags=["admin"])


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
    current_user=Depends(get_optional_current_user),
) -> OpportunityRead:
    target = db.get(Opportunity, payload.target_opportunity_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Target opportunity not found")
    duplicates_to_remove = db.query(Opportunity).filter(Opportunity.id.in_(payload.duplicate_opportunity_ids)).all()
    for duplicate in duplicates_to_remove:
        if duplicate.id == target.id:
            continue
        db.query(ProfileOpportunityStatus).filter(ProfileOpportunityStatus.opportunity_id == duplicate.id).update(
            {ProfileOpportunityStatus.opportunity_id: target.id}
        )
        db.query(OpportunityReminder).filter(OpportunityReminder.opportunity_id == duplicate.id).update(
            {OpportunityReminder.opportunity_id: target.id}
        )
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


@router.put("/opportunities/{opportunity_id}", response_model=OpportunityRead)
def edit_opportunity(
    opportunity_id: int,
    payload: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_current_user),
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
