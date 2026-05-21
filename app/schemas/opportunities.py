from datetime import date, datetime

from pydantic import BaseModel, Field, HttpUrl

from app.domain.enums import OpportunityType


class ExtractedRequirementRead(BaseModel):
    career_stages: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    required_degree: str = ""
    languages: list[str] = Field(default_factory=list)
    publication_expectation: str = ""
    mobility: str = ""
    citizenship: str = ""
    years_since_phd: int | None = None
    key_details: list[str] = Field(default_factory=list)
    why_it_matters: list[str] = Field(default_factory=list)
    snippets: list[str] = Field(default_factory=list)
    confidence: int = 0


class OpportunityBase(BaseModel):
    title: str
    opportunity_type: OpportunityType
    source: str
    url: HttpUrl
    summary: str = ""
    eligibility: str = ""
    disciplines: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    career_stages: list[str] = Field(default_factory=list)
    deadline: date | None = None


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityRead(OpportunityBase):
    id: int
    created_at: datetime | None = None
    extracted_requirements: ExtractedRequirementRead | None = None
    requirements_confidence: int = 0

    model_config = {"from_attributes": True}


class OpportunityListResponse(BaseModel):
    items: list[OpportunityRead] = Field(default_factory=list)
    total: int = 0
    limit: int = 50
    offset: int = 0


class OpportunityPreview(OpportunityBase):
    id: int | None = None
    requirements_confidence: int = 0


class OpportunityBulkImportRequest(BaseModel):
    source: str
    dry_run: bool = False
    opportunities: list[OpportunityCreate] = Field(default_factory=list)


class OpportunityBulkImportResult(BaseModel):
    batch_id: int | None = None
    imported_count: int
    updated_count: int
    skipped_count: int
    dry_run: bool
    opportunities: list[OpportunityPreview]
