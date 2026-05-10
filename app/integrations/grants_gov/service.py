import logging

from app.db.models import Opportunity
from app.db.session import SessionLocal
from app.integrations.grants_gov.client import GrantsGovClient
from app.integrations.grants_gov.mapper import normalize_grants_gov_hit
from app.modules.opportunities.mappers import to_opportunity_read
from app.schemas.ingestion import GrantsGovIngestionResult
from app.services.ingestion_audit import ensure_source, finish_batch, start_batch
from app.services.opportunity_search import index_opportunity_for_search


logger = logging.getLogger(__name__)


def ingest_grants_gov(
    keyword: str,
    limit: int = 10,
    import_results: bool = True,
    db=None,
    client: GrantsGovClient | None = None,
) -> GrantsGovIngestionResult:
    logger.info("grants.gov ingestion requested keyword=%s limit=%s import_results=%s", keyword, limit, import_results)
    if db is not None:
        return _ingest_grants_gov_in_db(
            db,
            keyword=keyword,
            limit=limit,
            import_results=import_results,
            client=client,
        )

    db = SessionLocal()
    try:
        return _ingest_grants_gov_in_db(
            db,
            keyword=keyword,
            limit=limit,
            import_results=import_results,
            client=client,
        )
    finally:
        db.close()


def _ingest_grants_gov_in_db(
    db,
    keyword: str,
    limit: int,
    import_results: bool,
    client: GrantsGovClient | None = None,
) -> GrantsGovIngestionResult:
    ensure_source(
        db,
        name="grants.gov",
        display_name="Grants.gov",
        base_url="https://www.grants.gov",
        source_type="api",
    )
    batch = start_batch(db, source_name="grants.gov", query=keyword, dry_run=not import_results)
    try:
        hits = (client or GrantsGovClient()).search(keyword, limit)
        logger.info("grants.gov search complete keyword=%s hit_count=%s", keyword, len(hits))
        normalized = [normalize_grants_gov_hit(hit, keyword) for hit in hits]

        imported: list[Opportunity] = []
        skipped_count = 0
        imported_count = 0
        if import_results:
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
                index_opportunity_for_search(opportunity)
        else:
            imported = normalized
            finish_batch(db, batch, imported_count=0, updated_count=0, skipped_count=0)
            db.commit()

        return GrantsGovIngestionResult(
            source="grants.gov",
            batch_id=batch.id,
            imported_count=imported_count if import_results else 0,
            skipped_count=skipped_count,
            opportunities=[to_opportunity_read(opportunity) for opportunity in imported],
        )
    except Exception:
        logger.exception("grants.gov ingestion failed keyword=%s batch_id=%s", keyword, batch.id)
        finish_batch(db, batch, imported_count=0, updated_count=0, skipped_count=0, error_count=1)
        db.commit()
        raise
