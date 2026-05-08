from pydantic import BaseModel, Field

from app.domain.enums import OpportunityType


class ResearcherProfileDetailsBase(BaseModel):
    research_summary: str = ""
    publications: list[str] = Field(default_factory=list)
    degrees: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    funding_interests: list[str] = Field(default_factory=list)
    unavailable_countries: list[str] = Field(default_factory=list)
    preferred_opportunity_types: list[OpportunityType] = Field(default_factory=list)
    min_duration_months: int | None = Field(default=None, ge=1)
    max_duration_months: int | None = Field(default=None, ge=1)


class ResearcherProfileDetailsUpsert(ResearcherProfileDetailsBase):
    pass


class ResearcherProfileDetailsRead(ResearcherProfileDetailsBase):
    id: int
    profile_id: int

    model_config = {"from_attributes": True}
