from datetime import date

from pydantic import BaseModel, HttpUrl

from app.db.models import OpportunityType


class ExtractedRequirementRead(BaseModel):
    career_stages: list[str] = []
    countries: list[str] = []
    required_degree: str = ""
    languages: list[str] = []
    publication_expectation: str = ""
    mobility: str = ""
    citizenship: str = ""
    years_since_phd: int | None = None
    snippets: list[str] = []
    confidence: int = 0


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
    extracted_requirements: ExtractedRequirementRead | None = None
    requirements_confidence: int = 0

    model_config = {"from_attributes": True}


class OpportunityPreview(OpportunityBase):
    id: int | None = None
    requirements_confidence: int = 0


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
