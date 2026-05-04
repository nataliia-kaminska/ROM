from dataclasses import dataclass, field
from typing import Any

from app.db.models import OpportunityType


@dataclass(frozen=True)
class NormalizedSourceItem:
    title: str
    url: str
    summary: str = ""
    eligibility: str = ""
    opportunity_type: OpportunityType | None = None
    disciplines: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    countries: list[str] = field(default_factory=list)
    career_stages: list[str] = field(default_factory=list)
    deadline: str = ""


class SourceConnector:
    source_name = "generic"
    display_name = "Generic Feed"
    default_type = OpportunityType.fellowship
    default_keywords: tuple[str, ...] = ()

    def normalize(self, item: dict[str, Any]) -> NormalizedSourceItem:
        keywords = _list_value(item.get("keywords") or item.get("tags") or item.get("category"))
        keywords.extend(value for value in self.default_keywords if value not in keywords)
        return NormalizedSourceItem(
            title=_first(item, "title", "name", "opportunityTitle") or "Untitled opportunity",
            url=_first(item, "url", "link", "href", "web_url"),
            summary=_first(item, "summary", "description", "abstract", "content"),
            eligibility=_first(item, "eligibility", "requirements"),
            opportunity_type=_opportunity_type(_first(item, "opportunity_type", "type")) or self.default_type,
            disciplines=_list_value(item.get("disciplines") or item.get("fields")),
            keywords=keywords,
            countries=_list_value(item.get("countries") or item.get("country")),
            career_stages=_list_value(item.get("career_stages") or item.get("careerStage")),
            deadline=_first(item, "deadline", "closeDate", "closing_date", "pubDate"),
        )


class EuraxessConnector(SourceConnector):
    source_name = "euraxess"
    display_name = "EURAXESS"
    default_type = OpportunityType.research_position
    default_keywords = ("mobility", "euraxess")

    def normalize(self, item: dict[str, Any]) -> NormalizedSourceItem:
        normalized = super().normalize(item)
        return NormalizedSourceItem(
            **{
                **normalized.__dict__,
                "url": normalized.url or _first(item, "applyUrl", "detailsUrl"),
                "summary": normalized.summary or _first(item, "offerDescription", "projectDescription"),
                "eligibility": normalized.eligibility or _first(item, "eligibilityCriteria", "requirements"),
                "countries": normalized.countries or _list_value(item.get("hosting_country") or item.get("hostCountry")),
                "career_stages": normalized.career_stages or _list_value(item.get("researcherProfile") or item.get("career_level")),
            }
        )


class DaadConnector(SourceConnector):
    source_name = "daad"
    display_name = "DAAD"
    default_type = OpportunityType.fellowship
    default_keywords = ("daad", "germany")

    def normalize(self, item: dict[str, Any]) -> NormalizedSourceItem:
        normalized = super().normalize(item)
        countries = normalized.countries or ["Germany"]
        return NormalizedSourceItem(
            **{
                **normalized.__dict__,
                "summary": normalized.summary or _first(item, "programmeDescription", "fundingPurpose"),
                "eligibility": normalized.eligibility or _first(item, "targetGroup", "requirements"),
                "countries": countries,
                "deadline": normalized.deadline or _first(item, "applicationDeadline"),
            }
        )


class FulbrightConnector(SourceConnector):
    source_name = "fulbright"
    display_name = "Fulbright"
    default_type = OpportunityType.fellowship
    default_keywords = ("fulbright", "exchange")

    def normalize(self, item: dict[str, Any]) -> NormalizedSourceItem:
        normalized = super().normalize(item)
        return NormalizedSourceItem(
            **{
                **normalized.__dict__,
                "summary": normalized.summary or _first(item, "award_description", "grant_activity"),
                "eligibility": normalized.eligibility or _first(item, "candidate_profile", "citizenship"),
                "countries": normalized.countries or _list_value(item.get("host_country") or item.get("country_name")),
                "deadline": normalized.deadline or _first(item, "deadline_date"),
            }
        )


class MscaConnector(SourceConnector):
    source_name = "msca"
    display_name = "Marie Sklodowska-Curie Actions"
    default_type = OpportunityType.fellowship
    default_keywords = ("msca", "horizon europe")

    def normalize(self, item: dict[str, Any]) -> NormalizedSourceItem:
        normalized = super().normalize(item)
        return NormalizedSourceItem(
            **{
                **normalized.__dict__,
                "summary": normalized.summary or _first(item, "callAbstract", "topicDescription"),
                "eligibility": normalized.eligibility or _first(item, "conditions", "admissibilityConditions"),
                "countries": normalized.countries or ["European Union"],
                "deadline": normalized.deadline or _first(item, "deadlineDate", "submissionDeadline"),
            }
        )


CONNECTORS: dict[str, SourceConnector] = {
    "euraxess": EuraxessConnector(),
    "daad": DaadConnector(),
    "fulbright": FulbrightConnector(),
    "msca": MscaConnector(),
}


def get_source_connector(source_name: str) -> SourceConnector:
    normalized = source_name.strip().lower().replace(" ", "_").replace("-", "_")
    for key, connector in CONNECTORS.items():
        if key in normalized:
            return connector
    return SourceConnector()


def _first(source: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = source.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        text = str(value).strip()
        if text:
            return text
    return ""


def _list_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).replace(";", ",").split(",") if item.strip()]


def _opportunity_type(value: str) -> OpportunityType | None:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    return OpportunityType(normalized) if normalized in {item.value for item in OpportunityType} else None
