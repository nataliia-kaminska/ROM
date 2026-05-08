from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.application.ports.ingestion import GrantsGovIngestionCommand
from app.application.use_cases.ingestion_strategies import ExternalFeedStrategy, GrantsGovStrategy
from app.schemas.ingestion import ExternalSourceImportRequest, ExternalSourceImportResult, GrantsGovIngestionResult


@dataclass
class GrantsGovIngestionUseCase:
    db: Session
    strategy: GrantsGovStrategy = GrantsGovStrategy()

    def execute(self, command: GrantsGovIngestionCommand) -> GrantsGovIngestionResult:
        return self.strategy.ingest(command, self.db)


@dataclass
class ExternalSourceIngestionUseCase:
    db: Session
    strategy: ExternalFeedStrategy = ExternalFeedStrategy()

    def execute(self, request: ExternalSourceImportRequest) -> ExternalSourceImportResult:
        return self.strategy.ingest(request, self.db)
