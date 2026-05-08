from dataclasses import dataclass, field
from datetime import date

from app.domain.enums import CareerStage, OpportunityType, ProfileOpportunityStatusValue


@dataclass(frozen=True)
class ResearcherProfileEntity:
    id: int | None
    full_name: str
    career_stage: CareerStage
    user_id: int | None = None
    email: str | None = None
    country: str | None = None
    disciplines: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    preferred_countries: tuple[str, ...] = ()


@dataclass(frozen=True)
class OpportunityEntity:
    id: int | None
    title: str
    opportunity_type: OpportunityType
    source: str
    url: str
    summary: str = ""
    eligibility: str = ""
    disciplines: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    countries: tuple[str, ...] = ()
    career_stages: tuple[str, ...] = ()
    deadline: date | None = None


@dataclass(frozen=True)
class RecommendationEntity:
    opportunity: OpportunityEntity
    match_score: int
    reasons: tuple[str, ...] = field(default_factory=tuple)
    user_status: ProfileOpportunityStatusValue | None = None
