from pydantic import BaseModel, Field

from app.domain.enums import CareerStage
from app.schemas.profiles import ResearcherProfileRead


class OrcidImportRequest(BaseModel):
    orcid_id: str
    career_stage: CareerStage = CareerStage.phd
    email: str | None = None
    disciplines: list[str] = Field(default_factory=list)
    preferred_countries: list[str] = Field(default_factory=list)


class OrcidImportPreview(BaseModel):
    full_name: str
    email: str | None = None
    country: str | None = None
    keywords: list[str]
    google_scholar_url: str | None = None
    linkedin_url: str | None = None
    external_urls: list[str]


class OrcidImportResult(BaseModel):
    imported: bool
    profile: ResearcherProfileRead
    preview: OrcidImportPreview
