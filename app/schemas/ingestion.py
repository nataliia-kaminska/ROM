from pydantic import BaseModel, Field

from app.schemas.opportunities import OpportunityRead


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
