from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import IngestionBatch, IngestionBatchStatus, OpportunitySource


def ensure_source(
    db: Session,
    name: str,
    display_name: str | None = None,
    base_url: str | None = None,
    source_type: str = "curated",
) -> OpportunitySource:
    source = db.query(OpportunitySource).filter(OpportunitySource.name == name).first()
    if source:
        return source

    source = OpportunitySource(
        name=name,
        display_name=display_name or name,
        base_url=base_url,
        source_type=source_type,
    )
    db.add(source)
    db.flush()
    return source


def start_batch(
    db: Session,
    source_name: str,
    query: str | None = None,
    dry_run: bool = False,
) -> IngestionBatch:
    batch = IngestionBatch(
        source_name=source_name,
        status=IngestionBatchStatus.dry_run if dry_run else IngestionBatchStatus.success,
        query=query,
    )
    db.add(batch)
    db.flush()
    return batch


def finish_batch(
    db: Session,
    batch: IngestionBatch,
    imported_count: int,
    updated_count: int,
    skipped_count: int,
    error_count: int = 0,
) -> IngestionBatch:
    batch.imported_count = imported_count
    batch.updated_count = updated_count
    batch.skipped_count = skipped_count
    batch.error_count = error_count
    batch.status = IngestionBatchStatus.failed if error_count else batch.status
    batch.finished_at = datetime.utcnow()

    source = db.query(OpportunitySource).filter(OpportunitySource.name == batch.source_name).first()
    if source and batch.status != IngestionBatchStatus.failed:
        source.last_synced_at = batch.finished_at

    return batch

