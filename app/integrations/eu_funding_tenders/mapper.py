from datetime import date, datetime
from typing import Any

from app.db.models import OpportunityType
from app.schemas.opportunities import OpportunityCreate


PORTAL_TOPIC_URL = "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-details/"
PORTAL_CALL_URL = "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/calls-for-proposals"


def normalize_eu_funding_hit(hit: dict[str, Any], source_name: str, fallback_keyword: str) -> OpportunityCreate:
    identifier = _field(hit, "identifier", "reference", "callIdentifier", "topicIdentifier")
    title = _field(hit, "title", "name") or identifier or "EU funding opportunity"
    framework = _field(hit, "frameworkProgramme", "programme", "programmePeriod")
    action_type = _field(hit, "typesOfAction", "type")
    call_name = _field(hit, "caName", "callTitle", "call")
    description = _field(hit, "description", "summary", "objective")
    deadline = _parse_date(_field(hit, "deadlineDate", "deadline", "endDate"))
    url = _topic_url(identifier)

    keywords = _dedupe([fallback_keyword, framework, action_type, call_name, "eu funding", "european commission"])
    disciplines = _dedupe([framework, call_name])

    return OpportunityCreate(
        title=title,
        opportunity_type=_type_from_source(source_name, action_type),
        source=source_name,
        url=url,
        summary=description or call_name or title,
        eligibility="See the EU Funding & Tenders Portal call page for admissibility and eligibility conditions.",
        disciplines=disciplines,
        keywords=keywords,
        countries=["European Union"],
        career_stages=[],
        deadline=deadline,
    )


def _field(source: dict[str, Any], *keys: str) -> str:
    for key in keys:
        if key not in source:
            continue
        text = _text(source[key])
        if text:
            return text
    fields = source.get("fields")
    if isinstance(fields, dict):
        return _field(fields, *keys)
    return ""


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, list):
        return ", ".join(_text(item) for item in value if _text(item)).strip()
    if isinstance(value, dict):
        for key in ("value", "label", "name", "title", "en"):
            if key in value:
                text = _text(value[key])
                if text:
                    return text
    return str(value).strip()


def _topic_url(identifier: str) -> str:
    if not identifier:
        return PORTAL_CALL_URL
    return f"{PORTAL_TOPIC_URL}{identifier.lower()}"


def _type_from_source(source_name: str, action_type: str) -> OpportunityType:
    source = source_name.casefold()
    text = action_type.casefold()
    if "erasmus" in source or "mobility" in text:
        return OpportunityType.exchange
    if "msca" in source or "fellowship" in text:
        return OpportunityType.fellowship
    return OpportunityType.grant


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    normalized = value[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return date.fromisoformat(normalized) if fmt == "%Y-%m-%d" else datetime.strptime(normalized, fmt).date()
        except ValueError:
            continue
    return None


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = " ".join((value or "").split())
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result
