from dataclasses import dataclass

from app.db.models import IngestionBatch, Opportunity, ResearcherProfile, ResearcherProfileDetails
from app.schemas.openalex import OpenAlexImportPreview
from app.schemas.orcid import OrcidImportPreview


@dataclass(frozen=True)
class BulkOpportunityImportResult:
    batch: IngestionBatch
    opportunities: list[Opportunity]
    imported_count: int
    updated_count: int
    skipped_count: int


@dataclass(frozen=True)
class OrcidProfileImportResult:
    profile: ResearcherProfile
    preview: OrcidImportPreview
    imported: bool


@dataclass(frozen=True)
class OpenAlexProfileImportResult:
    profile: ResearcherProfile
    details: ResearcherProfileDetails
    preview: OpenAlexImportPreview
