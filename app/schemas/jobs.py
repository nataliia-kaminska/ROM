from datetime import datetime
from typing import Any

from pydantic import BaseModel


class JobEnqueueRead(BaseModel):
    job_id: str
    queue: str
    status: str


class JobRead(BaseModel):
    id: str
    queue: str | None = None
    status: str
    description: str | None = None
    created_at: datetime | None = None
    enqueued_at: datetime | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    failure_reason: str | None = None
    result: Any = None


class QueueStatsRead(BaseModel):
    name: str
    queued_count: int
    failed_count: int
    started_count: int
    finished_count: int
    deferred_count: int
