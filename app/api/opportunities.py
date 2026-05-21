from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.models import Opportunity, User
from app.db.session import get_db
from app.modules.opportunities.mappers import to_opportunity_preview, to_opportunity_read
from app.services.serialization import unpack_list
from app.repositories import opportunities as opportunity_repository
from app.schemas.opportunities import (
    OpportunityBulkImportRequest,
    OpportunityBulkImportResult,
    OpportunityCreate,
    OpportunityListResponse,
    OpportunityRead,
)
from app.services import opportunities as opportunity_service
from app.services.opportunity_search import count_opportunities_with_search, list_opportunities_with_search
from app.services.source_quality import is_generic_provider_reference


router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.post("", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
def create_opportunity(
    payload: OpportunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> OpportunityRead:
    try:
        opportunity = opportunity_service.create_opportunity(db, payload)
    except opportunity_service.DuplicateOpportunityError as exc:
        raise HTTPException(status_code=409, detail="Opportunity with this URL already exists") from exc
    return to_opportunity_read(opportunity)


@router.get("", response_model=None)
def list_opportunities(
    source: str | None = None,
    opportunity_type: str | None = None,
    country: str | None = None,
    career_stage: str | None = None,
    keyword: str | None = None,
    active_only: bool = False,
    sort_by: str = Query(default="deadline", pattern="^(deadline|created_at|title|source)$"),
    sort_order: str = Query(default="asc", pattern="^(asc|desc)$"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    include_total: bool = False,
    db: Session = Depends(get_db),
) -> list[OpportunityRead] | OpportunityListResponse:
    opportunities = list_opportunities_with_search(
        db,
        source=source,
        opportunity_type=opportunity_type,
        country=country,
        career_stage=career_stage,
        keyword=keyword,
        active_only=active_only,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )
    items = [to_opportunity_read(opportunity) for opportunity in opportunities]
    if not include_total:
        return items
    total = count_opportunities_with_search(
        db,
        source=source,
        opportunity_type=opportunity_type,
        country=country,
        career_stage=career_stage,
        keyword=keyword,
        active_only=active_only,
    )
    return OpportunityListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/options")
def opportunity_filter_options(db: Session = Depends(get_db)) -> dict[str, list[str]]:
    rows = db.query(
        Opportunity.source,
        Opportunity.title,
        Opportunity.url,
        Opportunity.countries,
        Opportunity.keywords,
        Opportunity.disciplines,
        Opportunity.career_stages,
    ).all()
    rows = [row for row in rows if not is_generic_provider_reference(row.source, row.title, row.url)]
    return {
        "sources": _sorted_unique(row.source for row in rows),
        "countries": _sorted_unique(value for row in rows for value in unpack_list(row.countries)),
        "keywords": _sorted_unique(value for row in rows for value in unpack_list(row.keywords)),
        "disciplines": _sorted_unique(value for row in rows for value in unpack_list(row.disciplines)),
        "career_stages": _sorted_unique(value for row in rows for value in unpack_list(row.career_stages)),
    }


@router.post("/bulk-import", response_model=OpportunityBulkImportResult)
def bulk_import_opportunities(
    payload: OpportunityBulkImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
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


def _sorted_unique(values) -> list[str]:
    return sorted({str(value).strip() for value in values if str(value).strip()})
