from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.models import Opportunity
from app.db.session import get_db
from app.modules.opportunities.mappers import to_opportunity_read
from app.repositories import admin as admin_repository
from app.schemas.admin import AdminAnalyticsRead, AdminAuditLogRead, AdminDashboardRead, DuplicateMergeRequest, DuplicateOpportunityGroup
from app.schemas.opportunities import OpportunityCreate, OpportunityRead
from app.services.admin_ops import build_admin_analytics, duplicate_groups, log_admin_action
from app.services.admin_merge import merge_duplicate_opportunities
from app.services.opportunity_import import apply_opportunity_payload


router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/dashboard", response_model=AdminDashboardRead)
def dashboard(db: Session = Depends(get_db)) -> AdminDashboardRead:
    return AdminDashboardRead(
        sources=admin_repository.list_sources(db),
        recent_batches=admin_repository.list_recent_batches(db),
        failed_batches=admin_repository.list_failed_batches(db),
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
    return admin_repository.list_audit_log(db, limit=limit, offset=offset)


@router.get("/opportunities/duplicates", response_model=list[DuplicateOpportunityGroup])
def duplicates(db: Session = Depends(get_db)) -> list[DuplicateOpportunityGroup]:
    return [
        DuplicateOpportunityGroup(key=f"group-{index + 1}", opportunities=[to_opportunity_read(item) for item in group])
        for index, group in enumerate(duplicate_groups(db))
    ]


@router.post("/opportunities/merge", response_model=OpportunityRead)
def merge_duplicates(
    payload: DuplicateMergeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
) -> OpportunityRead:
    target = merge_duplicate_opportunities(
        db,
        payload.target_opportunity_id,
        payload.duplicate_opportunity_ids,
        current_user.id if current_user else None,
    )
    return to_opportunity_read(target)


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
    return to_opportunity_read(opportunity)
