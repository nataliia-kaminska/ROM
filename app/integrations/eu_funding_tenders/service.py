import logging

from app.db.models import Opportunity
from app.db.session import SessionLocal
from app.integrations.eu_funding_tenders.client import EUFundingTendersClient
from app.integrations.eu_funding_tenders.mapper import normalize_eu_funding_hit
from app.modules.opportunities.mappers import to_opportunity_preview
from app.schemas.ingestion import EUFundingTendersIngestionResult
from app.services.ingestion_audit import ensure_source, finish_batch, start_batch
from app.services.opportunity_import import import_opportunities
from app.services.opportunity_search import index_opportunity_for_search


logger = logging.getLogger(__name__)

EU_SCAN_PAGE_SIZE = 25
EU_SCAN_MAX_PAGES = 8


def ingest_eu_funding_tenders(
    keyword: str,
    source_name: str = "eu_funding_tenders",
    programme: str | None = None,
    limit: int = 10,
    import_results: bool = True,
    db=None,
    client: EUFundingTendersClient | None = None,
) -> EUFundingTendersIngestionResult:
    logger.info(
        "eu funding tenders ingestion requested source=%s keyword=%s programme=%s new_limit=%s import_results=%s",
        source_name,
        keyword,
        programme,
        limit,
        import_results,
    )
    if db is not None:
        return _ingest_in_db(db, keyword, source_name, programme, limit, import_results, client)

    db = SessionLocal()
    try:
        return _ingest_in_db(db, keyword, source_name, programme, limit, import_results, client)
    finally:
        db.close()


def _ingest_in_db(
    db,
    keyword: str,
    source_name: str,
    programme: str | None,
    limit: int,
    import_results: bool,
    client: EUFundingTendersClient | None = None,
) -> EUFundingTendersIngestionResult:
    display_name = _display_name(source_name)
    ensure_source(
        db,
        name=source_name,
        display_name=display_name,
        base_url="https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/home",
        source_type="api",
    )
    batch = start_batch(db, source_name=source_name, query=keyword, dry_run=not import_results)
    try:
        hits = _collect_candidate_hits(
            db=db,
            client=client or EUFundingTendersClient(),
            keyword=keyword,
            source_name=source_name,
            programme=programme,
            new_limit=limit,
        )
        logger.info("eu funding tenders search complete source=%s candidate_count=%s", source_name, len(hits))
        payloads = [normalize_eu_funding_hit(hit, source_name, keyword) for hit in hits]
        opportunities, imported_count, updated_count, skipped_count = import_opportunities(
            db=db,
            payloads=payloads,
            source=source_name,
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
            for opportunity in opportunities:
                db.refresh(opportunity)
                index_opportunity_for_search(opportunity)
        db.refresh(batch)
        return EUFundingTendersIngestionResult(
            source=source_name,
            batch_id=batch.id,
            imported_count=imported_count if import_results else 0,
            skipped_count=skipped_count,
            opportunities=[to_opportunity_preview(opportunity) for opportunity in opportunities],
        )
    except Exception:
        logger.exception("eu funding tenders ingestion failed source=%s keyword=%s batch_id=%s", source_name, keyword, batch.id)
        finish_batch(db, batch, imported_count=0, updated_count=0, skipped_count=0, error_count=1)
        db.commit()
        raise


def _collect_candidate_hits(
    db,
    client: EUFundingTendersClient,
    keyword: str,
    source_name: str,
    programme: str | None,
    new_limit: int,
) -> list[dict]:
    existing_urls = {
        row[0]
        for row in db.query(Opportunity.url)
        .filter(Opportunity.source == source_name)
        .all()
    }
    selected: list[dict] = []
    seen_urls = set(existing_urls)
    scanned = 0
    for page_number in range(1, EU_SCAN_MAX_PAGES + 1):
        hits = client.search(
            keyword=keyword,
            limit=EU_SCAN_PAGE_SIZE,
            programme=programme,
            page_number=page_number,
            page_size=EU_SCAN_PAGE_SIZE,
        )
        scanned += len(hits)
        if not hits:
            break
        for hit in hits:
            payload = normalize_eu_funding_hit(hit, source_name, keyword)
            url = str(payload.url)
            if url in seen_urls:
                continue
            seen_urls.add(url)
            selected.append(hit)
            if len(selected) >= new_limit:
                logger.info(
                    "eu funding tenders candidate scan complete source=%s pages=%s scanned=%s selected_new=%s existing_urls=%s",
                    source_name,
                    page_number,
                    scanned,
                    len(selected),
                    len(existing_urls),
                )
                return selected
    logger.info(
        "eu funding tenders candidate scan exhausted source=%s pages=%s scanned=%s selected_new=%s existing_urls=%s",
        source_name,
        EU_SCAN_MAX_PAGES,
        scanned,
        len(selected),
        len(existing_urls),
    )
    return selected


def _display_name(source_name: str) -> str:
    labels = {
        "eu_funding_tenders": "EU Funding & Tenders",
        "horizon_europe": "Horizon Europe",
        "erasmus": "Erasmus+",
        "msca": "Marie Sklodowska-Curie Actions",
    }
    return labels.get(source_name, source_name.replace("_", " ").title())
