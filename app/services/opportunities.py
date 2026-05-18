from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflictError
from app.db.models import IngestionBatch, Opportunity
from app.repositories import opportunities as opportunity_repository
from app.schemas.opportunities import OpportunityBulkImportRequest, OpportunityCreate
from app.services.embeddings import persist_opportunity_embedding_vector
from app.services.ingestion_audit import ensure_source, finish_batch, start_batch
from app.services.opportunity_import import build_opportunity, import_opportunities
from app.services.opportunity_search import index_opportunity_for_search
from app.services.results import BulkOpportunityImportResult


class DuplicateOpportunityError(ConflictError):
    pass


def create_opportunity(db: Session, payload: OpportunityCreate) -> Opportunity:
    existing = opportunity_repository.get_opportunity_by_url(db, str(payload.url))
    if existing:
        raise DuplicateOpportunityError(str(payload.url))

    opportunity = build_opportunity(payload)
    db.add(opportunity)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateOpportunityError(str(payload.url)) from exc
    db.refresh(opportunity)
    if settings.opportunity_embedding_on_import:
        persist_opportunity_embedding_vector(db, opportunity)
        db.commit()
        db.refresh(opportunity)
    index_opportunity_for_search(opportunity)
    return opportunity


def bulk_import_opportunities(
    db: Session,
    payload: OpportunityBulkImportRequest,
) -> BulkOpportunityImportResult:
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
            if settings.opportunity_embedding_on_import:
                persist_opportunity_embedding_vector(db, opportunity)
        if settings.opportunity_embedding_on_import:
            db.commit()
        for opportunity in opportunities:
            db.refresh(opportunity)
            index_opportunity_for_search(opportunity)
    db.refresh(batch)
    return BulkOpportunityImportResult(
        batch=batch,
        opportunities=opportunities,
        imported_count=imported_count,
        updated_count=updated_count,
        skipped_count=skipped_count,
    )
