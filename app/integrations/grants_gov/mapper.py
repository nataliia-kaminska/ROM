from datetime import date, datetime
from typing import Any

from app.db.models import Opportunity, OpportunityType
from app.services.serialization import pack_list


GRANTS_GOV_OPPORTUNITY_URL = "https://www.grants.gov/search-results-detail/"


def normalize_grants_gov_hit(hit: dict[str, Any], fallback_keyword: str) -> Opportunity:
    title = _first_text(hit, "title", "opportunityTitle", "opportunity_title", "synopsisTitle")
    opportunity_id = _first_text(hit, "id", "opportunityId", "opportunity_id", "oppId")
    number = _first_text(hit, "number", "opportunityNumber", "opportunity_number")
    agency = _first_text(hit, "agency", "agencyName", "agency_name")
    close_date = _parse_date(_first_text(hit, "closeDate", "close_date", "deadline"))
    summary = _first_text(hit, "description", "summary", "synopsis", "opportunityCategoryExplanation")
    url_id = opportunity_id or number
    url = f"{GRANTS_GOV_OPPORTUNITY_URL}{url_id}" if url_id else "https://www.grants.gov/search-grants"

    keywords = [fallback_keyword]
    if agency:
        keywords.append(agency)

    return Opportunity(
        title=title or "Untitled Grants.gov opportunity",
        opportunity_type=OpportunityType.grant,
        source="grants.gov",
        url=url,
        summary=summary,
        eligibility=_first_text(hit, "eligibility", "applicantEligibilityDescription"),
        disciplines=pack_list([]),
        keywords=pack_list(keywords),
        countries=pack_list(["United States"]),
        career_stages=pack_list([]),
        deadline=close_date,
    )


def _first_text(source: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = source.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _parse_date(value: str) -> date | None:
    if not value:
        return None

    normalized = value[:10]
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return date.fromisoformat(normalized) if fmt == "%Y-%m-%d" else datetime.strptime(value[:10], fmt).date()
        except ValueError:
            continue
    return None
