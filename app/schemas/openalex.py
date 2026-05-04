from pydantic import BaseModel, Field

from app.schemas.profile_details import ResearcherProfileDetailsRead
from app.schemas.profiles import ResearcherProfileRead


class OpenAlexImportRequest(BaseModel):
    profile_id: int
    openalex_author_id: str | None = None
    orcid_id: str | None = None
    max_works: int = Field(default=10, ge=1, le=50)


class OpenAlexImportPreview(BaseModel):
    display_name: str
    concepts: list[str]
    works: list[str]
    openalex_author_id: str | None = None


class OpenAlexImportResult(BaseModel):
    profile: ResearcherProfileRead
    details: ResearcherProfileDetailsRead
    preview: OpenAlexImportPreview
