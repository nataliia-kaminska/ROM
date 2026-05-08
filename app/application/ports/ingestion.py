from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.orm import Session

from app.schemas.ingestion import ExternalSourceImportRequest, ExternalSourceImportResult, GrantsGovIngestionResult


@dataclass(frozen=True)
class GrantsGovIngestionCommand:
    keyword: str
    limit: int = 10
    import_results: bool = True


class GrantsGovIngestionStrategy(Protocol):
    def ingest(self, command: GrantsGovIngestionCommand, db: Session) -> GrantsGovIngestionResult:
        ...


class ExternalSourceIngestionStrategy(Protocol):
    def ingest(self, request: ExternalSourceImportRequest, db: Session) -> ExternalSourceImportResult:
        ...
