from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ingestion import ExternalSourceImportRequest, ExternalSourceImportResult, GrantsGovIngestionResult, GrantsGovSearchRequest
from app.services.external_sources import import_external_source
from app.services.grants_gov_ingestion import ingest_grants_gov


router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/grants-gov/search", response_model=GrantsGovIngestionResult)
def search_grants_gov(payload: GrantsGovSearchRequest, db: Session = Depends(get_db)) -> GrantsGovIngestionResult:
    return ingest_grants_gov(
        keyword=payload.keyword,
        limit=payload.limit,
        import_results=payload.import_results,
        db=db,
    )


@router.post("/external-source/import", response_model=ExternalSourceImportResult)
def import_external_opportunity_source(
    payload: ExternalSourceImportRequest,
    db: Session = Depends(get_db),
) -> ExternalSourceImportResult:
    return import_external_source(payload, db)
