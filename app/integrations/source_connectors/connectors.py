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


class HorizonEuropeConnector(SourceConnector):
    source_name = "horizon_europe"
    display_name = "Horizon Europe"
    default_type = OpportunityType.grant
    default_keywords = ("horizon europe", "european commission", "research and innovation", "eu funding")

    def normalize(self, item: dict[str, Any]) -> NormalizedSourceItem:
        normalized = super().normalize(item)
        return NormalizedSourceItem(
            **{
                **normalized.__dict__,
                "summary": normalized.summary or _first(item, "callAbstract", "topicDescription", "objective", "description"),
                "eligibility": normalized.eligibility or _first(item, "conditions", "admissibilityConditions", "eligibilityConditions"),
                "countries": normalized.countries or ["European Union"],
                "disciplines": normalized.disciplines or _list_value(item.get("programme_part") or item.get("destination") or item.get("topicArea")),
                "deadline": normalized.deadline or _first(item, "deadlineDate", "submissionDeadline", "deadline"),
            }
        )


class ErasmusConnector(SourceConnector):
    source_name = "erasmus"
    display_name = "Erasmus+"
    default_type = OpportunityType.exchange
    default_keywords = ("erasmus+", "erasmus", "mobility", "european union")

    def normalize(self, item: dict[str, Any]) -> NormalizedSourceItem:
        normalized = super().normalize(item)
        text = f"{normalized.title} {normalized.summary} {normalized.eligibility}"
        return NormalizedSourceItem(
            **{
                **normalized.__dict__,
                "summary": normalized.summary or _first(item, "callAbstract", "description", "objective"),
                "eligibility": normalized.eligibility or _first(item, "who_can_apply", "target_group", "eligibleApplicants"),
                "countries": normalized.countries or ["European Union"],
                "career_stages": normalized.career_stages or _career_stages_from_text(text),
            }
        )


class NawaConnector(SourceConnector):
    source_name = "nawa"
    display_name = "NAWA"
    default_type = OpportunityType.fellowship
    default_keywords = ("nawa", "poland", "academic exchange", "scholarship")

    def normalize(self, item: dict[str, Any]) -> NormalizedSourceItem:
        normalized = super().normalize(item)
        text = f"{normalized.title} {normalized.summary} {normalized.eligibility}"
        return NormalizedSourceItem(
            **{
                **normalized.__dict__,
                "summary": normalized.summary or _first(item, "programmeDescription", "description", "lead"),
                "eligibility": normalized.eligibility or _first(item, "targetGroup", "requirements", "who_can_apply"),
                "countries": normalized.countries or ["Poland"],
                "career_stages": normalized.career_stages or _career_stages_from_text(text),
                "deadline": normalized.deadline or _first(item, "applicationDeadline", "deadlineDate"),
            }
        )


class NrfuConnector(SourceConnector):
    source_name = "nrfu"
    display_name = "National Research Foundation of Ukraine"
    default_type = OpportunityType.grant
    default_keywords = ("nrfu", "ukraine", "research grant")

    def normalize(self, item: dict[str, Any]) -> NormalizedSourceItem:
        normalized = super().normalize(item)
        return NormalizedSourceItem(
            **{
                **normalized.__dict__,
                "summary": normalized.summary or _first(item, "description", "excerpt", "content"),
                "eligibility": normalized.eligibility or _first(item, "conditions", "requirements"),
                "countries": normalized.countries or ["Ukraine"],
                "career_stages": normalized.career_stages
                or _career_stages_from_text(f"{normalized.title} {normalized.summary} {normalized.eligibility}"),
            }
        )


class NaukaGovUaConnector(SourceConnector):
    source_name = "nauka_gov_ua"
    display_name = "NAUKA opportunities"
    default_type = OpportunityType.grant
    default_keywords = ("nauka.gov.ua", "ukraine", "research")

    def normalize(self, item: dict[str, Any]) -> NormalizedSourceItem:
        normalized = super().normalize(item)
        return NormalizedSourceItem(
            **{
                **normalized.__dict__,
                "url": normalized.url or _first(item, "apply", "source_url"),
                "summary": normalized.summary or _first(item, "description", "excerpt"),
                "countries": normalized.countries or ["Ukraine"],
                "career_stages": normalized.career_stages
                or _career_stages_from_text(f"{normalized.title} {normalized.summary} {normalized.eligibility}"),
            }
        )


class HouseOfEuropeConnector(SourceConnector):
    source_name = "house_of_europe"
    display_name = "House of Europe"
    default_type = OpportunityType.grant
    default_keywords = ("house of europe", "ukraine", "eu")

    def normalize(self, item: dict[str, Any]) -> NormalizedSourceItem:
        normalized = super().normalize(item)
        item_type = _opportunity_type(_first(item, "type", "programmeType"))
        return NormalizedSourceItem(
            **{
                **normalized.__dict__,
                "opportunity_type": item_type or normalized.opportunity_type or self.default_type,
                "summary": normalized.summary or _first(item, "teaser", "description"),
                "eligibility": normalized.eligibility or _first(item, "who_can_apply", "target_group"),
                "countries": normalized.countries or ["Ukraine", "European Union"],
            }
        )


class ScienceForUkraineConnector(SourceConnector):
    source_name = "science_for_ukraine"
    display_name = "Science for Ukraine"
    default_type = OpportunityType.research_position
    default_keywords = ("science for ukraine", "ukraine", "support")

    def normalize(self, item: dict[str, Any]) -> NormalizedSourceItem:
        normalized = super().normalize(item)
        return NormalizedSourceItem(
            **{
                **normalized.__dict__,
                "summary": normalized.summary or _first(item, "description", "details"),
                "eligibility": normalized.eligibility or _first(item, "eligibility", "target_audience"),
                "countries": normalized.countries or _list_value(item.get("host_country") or item.get("location")),
                "career_stages": normalized.career_stages
                or _career_stages_from_text(f"{normalized.title} {normalized.summary} {normalized.eligibility}"),
            }
        )


class Msca4UkraineConnector(SourceConnector):
    source_name = "msca4ukraine"
    display_name = "MSCA4Ukraine"
    default_type = OpportunityType.fellowship
    default_keywords = ("msca4ukraine", "ukraine", "horizon europe", "msca")

    def normalize(self, item: dict[str, Any]) -> NormalizedSourceItem:
        normalized = super().normalize(item)
        return NormalizedSourceItem(
            **{
                **normalized.__dict__,
                "summary": normalized.summary or _first(item, "callAbstract", "description"),
                "eligibility": normalized.eligibility or _first(item, "conditions", "eligible_researchers"),
                "countries": normalized.countries or ["Ukraine", "European Union"],
                "deadline": normalized.deadline or _first(item, "deadlineDate", "submissionDeadline"),
            }
        )


class DaadUkraineConnector(DaadConnector):
    source_name = "daad_ukraine"
    display_name = "DAAD Ukraine"
    default_keywords = ("daad", "ukraine", "germany", "future ukraine")

    def normalize(self, item: dict[str, Any]) -> NormalizedSourceItem:
        normalized = super().normalize(item)
        return NormalizedSourceItem(
            **{
                **normalized.__dict__,
                "countries": normalized.countries or ["Germany", "Ukraine"],
                "career_stages": normalized.career_stages
                or _career_stages_from_text(f"{normalized.title} {normalized.summary} {normalized.eligibility}"),
            }
        )


class FulbrightUkraineConnector(FulbrightConnector):
    source_name = "fulbright_ukraine"
    display_name = "Fulbright Ukraine"
    default_keywords = ("fulbright", "ukraine", "exchange", "united states")

    def normalize(self, item: dict[str, Any]) -> NormalizedSourceItem:
        normalized = super().normalize(item)
        return NormalizedSourceItem(
            **{
                **normalized.__dict__,
                "countries": normalized.countries or ["United States", "Ukraine"],
                "career_stages": normalized.career_stages
                or _career_stages_from_text(f"{normalized.title} {normalized.summary} {normalized.eligibility}"),
            }
        )


CONNECTORS: dict[str, SourceConnector] = {
    "euraxess": EuraxessConnector(),
    "erasmus": ErasmusConnector(),
    "daad": DaadConnector(),
    "daad_ukraine": DaadUkraineConnector(),
    "fulbright": FulbrightConnector(),
    "fulbright_ukraine": FulbrightUkraineConnector(),
    "horizon_europe": HorizonEuropeConnector(),
    "horizon": HorizonEuropeConnector(),
    "house_of_europe": HouseOfEuropeConnector(),
    "msca": MscaConnector(),
    "msca4ukraine": Msca4UkraineConnector(),
    "nawa": NawaConnector(),
    "nauka_gov_ua": NaukaGovUaConnector(),
    "nrfu": NrfuConnector(),
    "science_for_ukraine": ScienceForUkraineConnector(),
}


def get_source_connector(source_name: str) -> SourceConnector:
    normalized = source_name.strip().lower().replace(" ", "_").replace("-", "_")
    exact_match = CONNECTORS.get(normalized)
    if exact_match:
        return exact_match
    for key, connector in sorted(CONNECTORS.items(), key=lambda candidate: len(candidate[0]), reverse=True):
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
    if normalized in {"scholarship", "award", "grant"}:
        return OpportunityType.fellowship if normalized == "scholarship" else OpportunityType.grant
    return OpportunityType(normalized) if normalized in {item.value for item in OpportunityType} else None


def _career_stages_from_text(value: str) -> list[str]:
    normalized = value.casefold()
    stages: list[str] = []
    stage_terms = {
        "masters": ("master", "masters", "master's"),
        "phd": ("phd", "doctoral", "doctorate", "candidate of sciences"),
        "postdoc": ("postdoc", "postdoctoral"),
        "faculty": ("professor", "lecturer", "teacher", "doctor of sciences"),
        "early-career": ("early career", "young scientist", "young researchers"),
    }
    for stage, terms in stage_terms.items():
        if any(term in normalized for term in terms):
            stages.append(stage)
    return stages
