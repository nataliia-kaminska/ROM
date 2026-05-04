from dataclasses import asdict
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Opportunity, OpportunityType
from app.db.session import get_db
from app.schemas.opportunities import (
    OpportunityBulkImportRequest,
    OpportunityBulkImportResult,
    OpportunityCreate,
    OpportunityPreview,
    OpportunityRead,
)
from app.services.ingestion_audit import ensure_source, finish_batch, start_batch
from app.services.opportunity_import import build_opportunity, import_opportunities
from app.services.requirements import extract_opportunity_requirements
from app.services.serialization import unpack_list


router = APIRouter(prefix="/opportunities", tags=["opportunities"])


def _to_read(opportunity: Opportunity) -> OpportunityRead:
    return OpportunityRead(
        id=opportunity.id,
        title=opportunity.title,
        opportunity_type=opportunity.opportunity_type,
        source=opportunity.source,
        url=opportunity.url,
        summary=opportunity.summary,
        eligibility=opportunity.eligibility,
        disciplines=unpack_list(opportunity.disciplines),
        keywords=unpack_list(opportunity.keywords),
        countries=unpack_list(opportunity.countries),
        career_stages=unpack_list(opportunity.career_stages),
        deadline=opportunity.deadline,
        extracted_requirements=asdict(extract_opportunity_requirements(opportunity)),
        requirements_confidence=opportunity.requirements_confidence,
    )


def _to_preview(opportunity: Opportunity) -> OpportunityPreview:
    return OpportunityPreview(
        id=opportunity.id,
        title=opportunity.title,
        opportunity_type=opportunity.opportunity_type,
        source=opportunity.source,
        url=opportunity.url,
        summary=opportunity.summary,
        eligibility=opportunity.eligibility,
        disciplines=unpack_list(opportunity.disciplines),
        keywords=unpack_list(opportunity.keywords),
        countries=unpack_list(opportunity.countries),
        career_stages=unpack_list(opportunity.career_stages),
        deadline=opportunity.deadline,
        requirements_confidence=opportunity.requirements_confidence,
    )


@router.post("", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
def create_opportunity(payload: OpportunityCreate, db: Session = Depends(get_db)) -> OpportunityRead:
    existing = db.query(Opportunity).filter(Opportunity.url == str(payload.url)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Opportunity with this URL already exists")

    opportunity = build_opportunity(payload)
    db.add(opportunity)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Opportunity with this URL already exists") from exc
    db.refresh(opportunity)
    return _to_read(opportunity)


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
    query = db.query(Opportunity)
    if source:
        query = query.filter(Opportunity.source == source)
    if opportunity_type:
        query = query.filter(Opportunity.opportunity_type == opportunity_type)
    if country:
        query = query.filter(Opportunity.countries.ilike(f"%{country}%"))
    if career_stage:
        query = query.filter(Opportunity.career_stages.ilike(f"%{career_stage}%"))
    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            Opportunity.title.ilike(pattern)
            | Opportunity.summary.ilike(pattern)
            | Opportunity.keywords.ilike(pattern)
            | Opportunity.disciplines.ilike(pattern)
        )
    if active_only:
        query = query.filter((Opportunity.deadline.is_(None)) | (Opportunity.deadline >= date.today()))

    opportunities = query.order_by(Opportunity.deadline.asc().nullslast()).offset(offset).limit(limit).all()
    return [_to_read(opportunity) for opportunity in opportunities]


@router.post("/bulk-import", response_model=OpportunityBulkImportResult)
def bulk_import_opportunities(
    payload: OpportunityBulkImportRequest,
    db: Session = Depends(get_db),
) -> OpportunityBulkImportResult:
    ensure_source(db, name=payload.source, display_name=payload.source, source_type="curated")
    batch = start_batch(db, source_name=payload.source, query="bulk-import", dry_run=payload.dry_run)
    opportunities, imported_count, updated_count, skipped_count = import_opportunities(
        db=db,
        payloads=payload.opportunities,
        source=payload.source,
        dry_run=payload.dry_run,
        commit=False,
    )
    finish_batch(
        db,
        batch,
        imported_count=imported_count if not payload.dry_run else 0,
        updated_count=updated_count if not payload.dry_run else 0,
        skipped_count=skipped_count,
    )
    db.commit()
    if not payload.dry_run:
        for opportunity in opportunities:
            db.refresh(opportunity)
    db.refresh(batch)

    return OpportunityBulkImportResult(
        batch_id=batch.id,
        imported_count=imported_count,
        updated_count=updated_count,
        skipped_count=skipped_count,
        dry_run=payload.dry_run,
        opportunities=[_to_preview(opportunity) for opportunity in opportunities],
    )


@router.get("/{opportunity_id}", response_model=OpportunityRead)
def get_opportunity(opportunity_id: int, db: Session = Depends(get_db)) -> OpportunityRead:
    opportunity = db.get(Opportunity, opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return _to_read(opportunity)
