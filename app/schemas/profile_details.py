from pydantic import BaseModel, Field

from app.db.models import OpportunityType


class ResearcherProfileDetailsBase(BaseModel):
    research_summary: str = ""
    publications: list[str] = []
    degrees: list[str] = []
    languages: list[str] = []
    funding_interests: list[str] = []
    unavailable_countries: list[str] = []
    preferred_opportunity_types: list[OpportunityType] = []
    min_duration_months: int | None = Field(default=None, ge=1)
    max_duration_months: int | None = Field(default=None, ge=1)


class ResearcherProfileDetailsUpsert(ResearcherProfileDetailsBase):
    pass


class ResearcherProfileDetailsRead(ResearcherProfileDetailsBase):
    id: int
    profile_id: int

    model_config = {"from_attributes": True}

