from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.models import IngestionBatch, OpportunitySource
from app.db.session import get_db
from app.schemas.ingestion_audit import IngestionBatchRead, OpportunitySourceRead


router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[OpportunitySourceRead])
def list_sources(db: Session = Depends(get_db)) -> list[OpportunitySourceRead]:
    return db.query(OpportunitySource).order_by(OpportunitySource.name.asc()).all()


@router.get("/batches", response_model=list[IngestionBatchRead])
def list_ingestion_batches(
    source_name: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[IngestionBatchRead]:
    query = db.query(IngestionBatch)
    if source_name:
        query = query.filter(IngestionBatch.source_name == source_name)
    return query.order_by(IngestionBatch.started_at.desc()).offset(offset).limit(limit).all()

