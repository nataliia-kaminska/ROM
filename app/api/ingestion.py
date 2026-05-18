from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_external_source_ingestion_use_case, get_grants_gov_ingestion_use_case, require_admin
from app.application.ports.ingestion import GrantsGovIngestionCommand
from app.application.use_cases.ingestion import ExternalSourceIngestionUseCase, GrantsGovIngestionUseCase
from app.db.session import get_db
from app.integrations.eu_funding_tenders.service import ingest_eu_funding_tenders
from app.schemas.ingestion import (
    EUFundingTendersIngestionResult,
    EUFundingTendersSearchRequest,
    ExternalSourceImportRequest,
    ExternalSourceImportResult,
    GrantsGovIngestionResult,
    GrantsGovSearchRequest,
)


router = APIRouter(prefix="/ingestion", tags=["ingestion"], dependencies=[Depends(require_admin)])


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


@router.post("/eu-funding-tenders/search", response_model=EUFundingTendersIngestionResult)
def search_eu_funding_tenders(
    payload: EUFundingTendersSearchRequest,
    db: Session = Depends(get_db),
) -> EUFundingTendersIngestionResult:
    return ingest_eu_funding_tenders(
        keyword=payload.keyword,
        source_name=payload.source_name,
        programme=payload.programme,
        limit=payload.limit,
        import_results=payload.import_results,
        db=db,
    )
