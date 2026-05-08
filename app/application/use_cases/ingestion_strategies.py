from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.application.ports.ingestion import GrantsGovIngestionCommand
from app.schemas.ingestion import ExternalSourceImportRequest, ExternalSourceImportResult, GrantsGovIngestionResult
from app.services.external_sources import import_external_source
from app.services.grants_gov_ingestion import ingest_grants_gov


@dataclass(frozen=True)
class GrantsGovStrategy:
    def ingest(self, command: GrantsGovIngestionCommand, db: Session) -> GrantsGovIngestionResult:
        return ingest_grants_gov(
            keyword=command.keyword,
            limit=command.limit,
            import_results=command.import_results,
            db=db,
        )


@dataclass(frozen=True)
class ExternalFeedStrategy:
    def ingest(self, request: ExternalSourceImportRequest, db: Session) -> ExternalSourceImportResult:
        return import_external_source(request, db)
