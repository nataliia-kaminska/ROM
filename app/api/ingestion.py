from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.opportunities import _to_read
from app.db.models import Opportunity
from app.db.session import get_db
from app.schemas.ingestion import GrantsGovIngestionResult, GrantsGovSearchRequest
from app.services.grants_gov import GrantsGovClient, normalize_grants_gov_hit
from app.services.ingestion_audit import ensure_source, finish_batch, start_batch


router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/grants-gov/search", response_model=GrantsGovIngestionResult)
def search_grants_gov(payload: GrantsGovSearchRequest, db: Session = Depends(get_db)) -> GrantsGovIngestionResult:
    ensure_source(
        db,
        name="grants.gov",
        display_name="Grants.gov",
        base_url="https://www.grants.gov",
        source_type="api",
    )
    batch = start_batch(db, source_name="grants.gov", query=payload.keyword, dry_run=not payload.import_results)
    hits = GrantsGovClient().search(payload.keyword, payload.limit)
    normalized = [normalize_grants_gov_hit(hit, payload.keyword) for hit in hits]

    imported: list[Opportunity] = []
    skipped_count = 0
    imported_count = 0
    if payload.import_results:
        for opportunity in normalized:
            existing = db.query(Opportunity).filter(Opportunity.url == opportunity.url).first()
            if existing:
                imported.append(existing)
                skipped_count += 1
                continue
            db.add(opportunity)
            db.flush()
            imported.append(opportunity)
            imported_count += 1
        finish_batch(db, batch, imported_count=imported_count, updated_count=0, skipped_count=skipped_count)
        db.commit()
        for opportunity in imported:
            db.refresh(opportunity)
    else:
        imported = normalized
        finish_batch(db, batch, imported_count=0, updated_count=0, skipped_count=0)
        db.commit()

    return GrantsGovIngestionResult(
        source="grants.gov",
        batch_id=batch.id,
        imported_count=imported_count if payload.import_results else 0,
        skipped_count=skipped_count,
        opportunities=[_to_read(opportunity) for opportunity in imported],
    )
