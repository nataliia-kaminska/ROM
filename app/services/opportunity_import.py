from sqlalchemy.orm import Session

from app.db.models import Opportunity
from app.schemas.opportunities import OpportunityCreate
from app.services.embeddings import ensure_opportunity_embedding
from app.services.requirements import refresh_opportunity_requirements
from app.services.serialization import pack_list, unpack_list


def build_opportunity(payload: OpportunityCreate, source: str | None = None) -> Opportunity:
    opportunity = Opportunity(
        title=_clean_text(payload.title),
        opportunity_type=payload.opportunity_type,
        source=_clean_text(source or payload.source),
        url=_normalize_url(str(payload.url)),
        summary=_clean_text(payload.summary),
        eligibility=_clean_text(payload.eligibility),
        disciplines=pack_list(_clean_list(payload.disciplines)),
        keywords=pack_list(_clean_list(payload.keywords)),
        countries=pack_list(_clean_list(payload.countries)),
        career_stages=pack_list(_clean_list(payload.career_stages)),
        deadline=payload.deadline,
    )
    refresh_opportunity_requirements(opportunity)
    ensure_opportunity_embedding(opportunity)
    return opportunity


def apply_opportunity_payload(opportunity: Opportunity, payload: OpportunityCreate, source: str | None = None) -> None:
    opportunity.title = _clean_text(payload.title)
    opportunity.opportunity_type = payload.opportunity_type
    opportunity.source = _clean_text(source or payload.source)
    opportunity.url = _normalize_url(str(payload.url))
    opportunity.summary = _clean_text(payload.summary)
    opportunity.eligibility = _clean_text(payload.eligibility)
    opportunity.disciplines = pack_list(_merge_lists(unpack_list(opportunity.disciplines), payload.disciplines))
    opportunity.keywords = pack_list(_merge_lists(unpack_list(opportunity.keywords), payload.keywords))
    opportunity.countries = pack_list(_merge_lists(unpack_list(opportunity.countries), payload.countries))
    opportunity.career_stages = pack_list(_merge_lists(unpack_list(opportunity.career_stages), payload.career_stages))
    opportunity.deadline = payload.deadline
    opportunity.opportunity_embedding = ""
    refresh_opportunity_requirements(opportunity)
    ensure_opportunity_embedding(opportunity)


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
        url = _normalize_url(str(payload.url))
        if url in seen_urls:
            skipped_count += 1
            continue
        seen_urls.add(url)

        existing = db.query(Opportunity).filter(Opportunity.url == url).first()
        if existing is None:
            existing = _find_content_duplicate(db, payload, source)
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


def _find_content_duplicate(db: Session, payload: OpportunityCreate, source: str) -> Opportunity | None:
    title_key = _normalized_title(payload.title)
    source_key = _clean_text(source).casefold()
    candidates = db.query(Opportunity).filter(Opportunity.source == source).all()
    for candidate in candidates:
        if _normalized_title(candidate.title) == title_key and candidate.source.casefold() == source_key:
            return candidate
    return None


def _clean_text(value: str | None) -> str:
    return " ".join((value or "").strip().split())


def _normalize_url(value: str) -> str:
    cleaned = _clean_text(value)
    if cleaned.endswith("/") and "?" not in cleaned:
        return cleaned.rstrip("/")
    return cleaned


def _normalized_title(value: str) -> str:
    return "".join(character for character in _clean_text(value).casefold() if character.isalnum())


def _clean_list(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = _clean_text(value)
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def _merge_lists(existing: list[str], incoming: list[str]) -> list[str]:
    return _clean_list([*existing, *incoming])
