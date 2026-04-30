from pydantic import BaseModel

from app.db.models import CareerStage
from app.schemas.profiles import ResearcherProfileRead


class OrcidImportRequest(BaseModel):
    orcid_id: str
    career_stage: CareerStage = CareerStage.phd
    email: str | None = None
    disciplines: list[str] = []
    preferred_countries: list[str] = []


class OrcidImportPreview(BaseModel):
    full_name: str
    country: str | None = None
    keywords: list[str]
    google_scholar_url: str | None = None
    linkedin_url: str | None = None
    external_urls: list[str]


class OrcidImportResult(BaseModel):
    imported: bool
    profile: ResearcherProfileRead
    preview: OrcidImportPreview
