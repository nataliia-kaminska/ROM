from pydantic import BaseModel, Field
from pydantic import HttpUrl

from app.schemas.opportunities import OpportunityPreview, OpportunityRead


class GrantsGovSearchRequest(BaseModel):
    keyword: str = Field(..., min_length=2)
    limit: int = Field(default=10, ge=1, le=50)
    import_results: bool = True


class GrantsGovIngestionResult(BaseModel):
    source: str
    batch_id: int | None = None
    imported_count: int
    skipped_count: int
    opportunities: list[OpportunityRead]


class ExternalSourceImportRequest(BaseModel):
    source_name: str = Field(..., min_length=2)
    source_url: HttpUrl
    source_kind: str = Field(default="rss", pattern="^(rss|json)$")
    import_results: bool = True
    limit: int = Field(default=25, ge=1, le=100)
    default_opportunity_type: str = "fellowship"
    default_country: str | None = None
    default_career_stage: str | None = None
    default_discipline: str | None = None
    keyword: str | None = None


class ExternalSourceImportResult(BaseModel):
    source: str
    batch_id: int | None = None
    imported_count: int
    updated_count: int
    skipped_count: int
    opportunities: list[OpportunityPreview]
