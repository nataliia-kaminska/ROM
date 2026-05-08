from fastapi import APIRouter, Depends

from app.api.dependencies import get_external_source_ingestion_use_case, get_grants_gov_ingestion_use_case
from app.application.ports.ingestion import GrantsGovIngestionCommand
from app.application.use_cases.ingestion import ExternalSourceIngestionUseCase, GrantsGovIngestionUseCase
from app.schemas.ingestion import ExternalSourceImportRequest, ExternalSourceImportResult, GrantsGovIngestionResult, GrantsGovSearchRequest


router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/grants-gov/search", response_model=GrantsGovIngestionResult)
def search_grants_gov(
    payload: GrantsGovSearchRequest,
    use_case: GrantsGovIngestionUseCase = Depends(get_grants_gov_ingestion_use_case),
) -> GrantsGovIngestionResult:
    return use_case.execute(
        GrantsGovIngestionCommand(
        keyword=payload.keyword,
        limit=payload.limit,
        import_results=payload.import_results,
        ),
    )


@router.post("/external-source/import", response_model=ExternalSourceImportResult)
def import_external_opportunity_source(
    payload: ExternalSourceImportRequest,
    use_case: ExternalSourceIngestionUseCase = Depends(get_external_source_ingestion_use_case),
) -> ExternalSourceImportResult:
    return use_case.execute(payload)
