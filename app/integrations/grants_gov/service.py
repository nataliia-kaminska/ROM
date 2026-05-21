import logging

from app.db.models import Opportunity
from app.db.session import SessionLocal
from app.integrations.grants_gov.client import GrantsGovClient
from app.integrations.grants_gov.mapper import normalize_grants_gov_hit
from app.modules.opportunities.mappers import to_opportunity_read
from app.schemas.ingestion import GrantsGovIngestionResult
from app.schemas.opportunities import OpportunityCreate
from app.services.embeddings import persist_opportunity_embedding_vector
from app.services.ingestion_audit import ensure_source, finish_batch, start_batch
from app.services.opportunity_import import import_opportunities
from app.services.opportunity_search import index_opportunity_for_search


logger = logging.getLogger(__name__)
GRANTS_GOV_SCAN_PAGE_SIZE = 25
GRANTS_GOV_SCAN_MAX_PAGES = 8


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
        source_client = client or GrantsGovClient()
        normalized = (
            _collect_new_grants_gov_payloads(db, source_client, keyword, limit)
            if import_results
            else [normalize_grants_gov_hit(hit, keyword) for hit in source_client.search(keyword, limit=limit, offset=0)]
        )
        logger.info("grants.gov normalized keyword=%s candidate_count=%s import_results=%s", keyword, len(normalized), import_results)
        imported, imported_count, updated_count, skipped_count = import_opportunities(
            db=db,
            payloads=normalized,
            source="grants.gov",
            dry_run=not import_results,
            commit=False,
        )
        finish_batch(
            db,
            batch,
            imported_count=imported_count if import_results else 0,
            updated_count=updated_count if import_results else 0,
            skipped_count=skipped_count,
        )
        db.commit()
        if import_results:
            for opportunity in imported:
                db.refresh(opportunity)
                persist_opportunity_embedding_vector(db, opportunity)
                index_opportunity_for_search(opportunity)
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


def _collect_new_grants_gov_payloads(
    db,
    client: GrantsGovClient,
    keyword: str,
    new_limit: int,
) -> list[OpportunityCreate]:
    existing_urls = {
        row[0]
        for row in db.query(Opportunity.url).filter(Opportunity.source == "grants.gov").all()
        if row[0]
    }
    seen_urls = set(existing_urls)
    selected: list[OpportunityCreate] = []
    scanned_count = 0

    for page in range(GRANTS_GOV_SCAN_MAX_PAGES):
        offset = page * GRANTS_GOV_SCAN_PAGE_SIZE
        hits = client.search(keyword, limit=GRANTS_GOV_SCAN_PAGE_SIZE, offset=offset)
        scanned_count += len(hits)
        if not hits:
            break
        for hit in hits:
            payload = normalize_grants_gov_hit(hit, keyword)
            url = str(payload.url).rstrip("/")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            selected.append(payload)
            if len(selected) >= new_limit:
                logger.info(
                    "grants.gov collected new payloads keyword=%s requested=%s selected=%s scanned=%s",
                    keyword,
                    new_limit,
                    len(selected),
                    scanned_count,
                )
                return selected

    logger.info(
        "grants.gov collected new payloads keyword=%s requested=%s selected=%s scanned=%s",
        keyword,
        new_limit,
        len(selected),
        scanned_count,
    )
    return selected
