from datetime import datetime

from pydantic import BaseModel

from app.db.models import IngestionBatchStatus


class OpportunitySourceRead(BaseModel):
    id: int
    name: str
    display_name: str
    base_url: str | None
    source_type: str
    notes: str
    last_synced_at: datetime | None

    model_config = {"from_attributes": True}


class IngestionBatchRead(BaseModel):
    id: int
    source_name: str
    status: IngestionBatchStatus
    imported_count: int
    updated_count: int
    skipped_count: int
    error_count: int
    query: str | None
    started_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}

