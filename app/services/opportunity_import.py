from sqlalchemy.orm import Session

from app.db.models import Opportunity
from app.schemas.opportunities import OpportunityCreate
from app.services.serialization import pack_list


def build_opportunity(payload: OpportunityCreate, source: str | None = None) -> Opportunity:
    return Opportunity(
        title=payload.title,
        opportunity_type=payload.opportunity_type,
        source=source or payload.source,
        url=str(payload.url),
        summary=payload.summary,
        eligibility=payload.eligibility,
        disciplines=pack_list(payload.disciplines),
        keywords=pack_list(payload.keywords),
        countries=pack_list(payload.countries),
        career_stages=pack_list(payload.career_stages),
        deadline=payload.deadline,
    )


def apply_opportunity_payload(opportunity: Opportunity, payload: OpportunityCreate, source: str | None = None) -> None:
    opportunity.title = payload.title
    opportunity.opportunity_type = payload.opportunity_type
    opportunity.source = source or payload.source
    opportunity.summary = payload.summary
    opportunity.eligibility = payload.eligibility
    opportunity.disciplines = pack_list(payload.disciplines)
    opportunity.keywords = pack_list(payload.keywords)
    opportunity.countries = pack_list(payload.countries)
    opportunity.career_stages = pack_list(payload.career_stages)
    opportunity.deadline = payload.deadline


def import_opportunities(
    db: Session,
    payloads: list[OpportunityCreate],
    source: str,
    dry_run: bool = False,
    commit: bool = True,
) -> tuple[list[Opportunity], int, int, int]:
    imported_count = 0
    updated_count = 0
    skipped_count = 0
    processed: list[Opportunity] = []

    seen_urls: set[str] = set()
    for payload in payloads:
        url = str(payload.url)
        if url in seen_urls:
            skipped_count += 1
            continue
        seen_urls.add(url)

        existing = db.query(Opportunity).filter(Opportunity.url == url).first()
        if existing:
            if not dry_run:
                apply_opportunity_payload(existing, payload, source)
            processed.append(existing)
            updated_count += 1
            continue

        opportunity = build_opportunity(payload, source)
        processed.append(opportunity)
        imported_count += 1
        if not dry_run:
            db.add(opportunity)

    if not dry_run and commit:
        db.commit()
        for opportunity in processed:
            db.refresh(opportunity)

    return processed, imported_count, updated_count, skipped_count
