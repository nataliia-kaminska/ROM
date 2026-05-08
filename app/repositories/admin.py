from sqlalchemy.orm import Session

from app.db.models import AdminAuditLog, IngestionBatch, IngestionBatchStatus, OpportunitySource


def list_sources(db: Session) -> list[OpportunitySource]:
    return db.query(OpportunitySource).order_by(OpportunitySource.name.asc()).all()


def list_recent_batches(db: Session, limit: int = 10) -> list[IngestionBatch]:
    return db.query(IngestionBatch).order_by(IngestionBatch.started_at.desc()).limit(limit).all()


def list_failed_batches(db: Session, limit: int = 10) -> list[IngestionBatch]:
    return (
        db.query(IngestionBatch)
        .filter(IngestionBatch.status == IngestionBatchStatus.failed)
        .order_by(IngestionBatch.started_at.desc())
        .limit(limit)
        .all()
    )


def list_audit_log(db: Session, limit: int = 50, offset: int = 0) -> list[AdminAuditLog]:
    return db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).offset(offset).limit(limit).all()
