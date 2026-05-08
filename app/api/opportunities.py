from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.models import OpportunityType
from app.db.session import get_db
from app.modules.opportunities.mappers import to_opportunity_preview, to_opportunity_read
from app.repositories import opportunities as opportunity_repository
from app.schemas.opportunities import (
    OpportunityBulkImportRequest,
    OpportunityBulkImportResult,
    OpportunityCreate,
    OpportunityRead,
)
from app.services import opportunities as opportunity_service
from app.services.opportunity_search import list_opportunities_with_search


router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.post("", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
def create_opportunity(payload: OpportunityCreate, db: Session = Depends(get_db)) -> OpportunityRead:
    try:
        opportunity = opportunity_service.create_opportunity(db, payload)
    except opportunity_service.DuplicateOpportunityError as exc:
        raise HTTPException(status_code=409, detail="Opportunity with this URL already exists") from exc
    return to_opportunity_read(opportunity)


@router.get("", response_model=list[OpportunityRead])
def list_opportunities(
    source: str | None = None,
    opportunity_type: OpportunityType | None = None,
    country: str | None = None,
    career_stage: str | None = None,
    keyword: str | None = None,
    active_only: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[OpportunityRead]:
    opportunities = list_opportunities_with_search(
        db,
        source=source,
        opportunity_type=opportunity_type,
        country=country,
        career_stage=career_stage,
        keyword=keyword,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )
    return [to_opportunity_read(opportunity) for opportunity in opportunities]


@router.post("/bulk-import", response_model=OpportunityBulkImportResult)
def bulk_import_opportunities(
    payload: OpportunityBulkImportRequest,
    db: Session = Depends(get_db),
) -> OpportunityBulkImportResult:
    result = opportunity_service.bulk_import_opportunities(
        db,
        payload,
    )

    return OpportunityBulkImportResult(
        batch_id=result.batch.id,
        imported_count=result.imported_count,
        updated_count=result.updated_count,
        skipped_count=result.skipped_count,
        dry_run=payload.dry_run,
        opportunities=[to_opportunity_preview(opportunity) for opportunity in result.opportunities],
    )


@router.get("/{opportunity_id}", response_model=OpportunityRead)
def get_opportunity(opportunity_id: int, db: Session = Depends(get_db)) -> OpportunityRead:
    opportunity = opportunity_repository.get_opportunity(db, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return to_opportunity_read(opportunity)
