from datetime import date

from pydantic import BaseModel, HttpUrl

from app.db.models import OpportunityType


class OpportunityBase(BaseModel):
    title: str
    opportunity_type: OpportunityType
    source: str
    url: HttpUrl
    summary: str = ""
    eligibility: str = ""
    disciplines: list[str] = []
    keywords: list[str] = []
    countries: list[str] = []
    career_stages: list[str] = []
    deadline: date | None = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityRead(OpportunityBase):
    id: int

    model_config = {"from_attributes": True}


class OpportunityPreview(OpportunityBase):
    id: int | None = None


class OpportunityBulkImportRequest(BaseModel):
    source: str
    dry_run: bool = False
    opportunities: list[OpportunityCreate]


class OpportunityBulkImportResult(BaseModel):
    batch_id: int | None = None
    imported_count: int
    updated_count: int
    skipped_count: int
    dry_run: bool
    opportunities: list[OpportunityPreview]
