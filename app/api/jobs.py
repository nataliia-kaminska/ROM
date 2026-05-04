from fastapi import APIRouter, HTTPException, Query, status
from redis.exceptions import RedisError
from rq import Queue, Retry
from rq.job import Job
from rq.registry import DeferredJobRegistry, FailedJobRegistry, FinishedJobRegistry, StartedJobRegistry

from app.schemas.ingestion import GrantsGovSearchRequest
from app.schemas.jobs import JobEnqueueRead, JobRead, QueueStatsRead
from app.workers.jobs import (
    ingest_grants_gov_job,
    refresh_all_embeddings_job,
    scan_due_reminders_job,
    send_high_match_alerts_job,
    send_weekly_digest_job,
)
from app.workers.queues import EMBEDDINGS_QUEUE, INGESTION_QUEUE, QUEUE_NAMES, REMINDERS_QUEUE, get_queue


router = APIRouter(prefix="/jobs", tags=["jobs"])


def _queue_unavailable(exc: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Job queue unavailable: {exc}")


def _to_job_read(job: Job) -> JobRead:
    return JobRead(
        id=job.id,
        queue=job.origin,
        status=job.get_status(refresh=True),
        description=job.description,
        created_at=job.created_at,
        enqueued_at=job.enqueued_at,
        started_at=job.started_at,
        ended_at=job.ended_at,
        failure_reason=job.exc_info,
        result=job.return_value(refresh=True) if job.is_finished else None,
    )


@router.post("/ingestion/grants-gov", response_model=JobEnqueueRead, status_code=status.HTTP_202_ACCEPTED)
def enqueue_grants_gov_ingestion(payload: GrantsGovSearchRequest) -> JobEnqueueRead:
    try:
        queue = get_queue(INGESTION_QUEUE)
        job = queue.enqueue(
            ingest_grants_gov_job,
            kwargs={"keyword": payload.keyword, "limit": payload.limit, "import_results": payload.import_results},
            retry=Retry(max=3, interval=[60, 300, 900]),
            job_timeout="15m",
            description=f"Grants.gov search for {payload.keyword}",
        )
        return JobEnqueueRead(job_id=job.id, queue=queue.name, status=job.get_status(refresh=True))
    except RedisError as exc:
        raise _queue_unavailable(exc) from exc


@router.post("/reminders/scan", response_model=JobEnqueueRead, status_code=status.HTTP_202_ACCEPTED)
def enqueue_reminder_scan() -> JobEnqueueRead:
    try:
        queue = get_queue(REMINDERS_QUEUE)
        job = queue.enqueue(
            scan_due_reminders_job,
            retry=Retry(max=3, interval=[60, 300, 900]),
            job_timeout="5m",
            description="Scan due opportunity reminders",
        )
        return JobEnqueueRead(job_id=job.id, queue=queue.name, status=job.get_status(refresh=True))
    except RedisError as exc:
        raise _queue_unavailable(exc) from exc


@router.post("/notifications/weekly-digest", response_model=JobEnqueueRead, status_code=status.HTTP_202_ACCEPTED)
def enqueue_weekly_digest() -> JobEnqueueRead:
    try:
        queue = get_queue(REMINDERS_QUEUE)
        job = queue.enqueue(
            send_weekly_digest_job,
            retry=Retry(max=3, interval=[60, 300, 900]),
            job_timeout="10m",
            description="Send weekly recommendation digest",
        )
        return JobEnqueueRead(job_id=job.id, queue=queue.name, status=job.get_status(refresh=True))
    except RedisError as exc:
        raise _queue_unavailable(exc) from exc


@router.post("/notifications/high-match-alerts", response_model=JobEnqueueRead, status_code=status.HTTP_202_ACCEPTED)
def enqueue_high_match_alerts() -> JobEnqueueRead:
    try:
        queue = get_queue(REMINDERS_QUEUE)
        job = queue.enqueue(
            send_high_match_alerts_job,
            retry=Retry(max=3, interval=[60, 300, 900]),
            job_timeout="10m",
            description="Send high-match opportunity alerts",
        )
        return JobEnqueueRead(job_id=job.id, queue=queue.name, status=job.get_status(refresh=True))
    except RedisError as exc:
        raise _queue_unavailable(exc) from exc


@router.post("/embeddings/refresh", response_model=JobEnqueueRead, status_code=status.HTTP_202_ACCEPTED)
def enqueue_embedding_refresh() -> JobEnqueueRead:
    try:
        queue = get_queue(EMBEDDINGS_QUEUE)
        job = queue.enqueue(
            refresh_all_embeddings_job,
            retry=Retry(max=3, interval=[60, 300, 900]),
            job_timeout="15m",
            description="Refresh profile and opportunity embeddings",
        )
        return JobEnqueueRead(job_id=job.id, queue=queue.name, status=job.get_status(refresh=True))
    except RedisError as exc:
        raise _queue_unavailable(exc) from exc


@router.get("", response_model=list[QueueStatsRead])
def list_queues() -> list[QueueStatsRead]:
    try:
        stats = []
        for name in QUEUE_NAMES:
            queue = get_queue(name)
            stats.append(
                QueueStatsRead(
                    name=name,
                    queued_count=queue.count,
                    failed_count=len(FailedJobRegistry(queue=queue)),
                    started_count=len(StartedJobRegistry(queue=queue)),
                    finished_count=len(FinishedJobRegistry(queue=queue)),
                    deferred_count=len(DeferredJobRegistry(queue=queue)),
                )
            )
        return stats
    except RedisError as exc:
        raise _queue_unavailable(exc) from exc


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: str, queue_name: str | None = Query(default=None)) -> JobRead:
    try:
        queues = [get_queue(queue_name)] if queue_name else [get_queue(name) for name in QUEUE_NAMES]
        for queue in queues:
            try:
                return _to_job_read(Job.fetch(job_id, connection=queue.connection))
            except Exception:
                continue
        raise HTTPException(status_code=404, detail="Job not found")
    except RedisError as exc:
        raise _queue_unavailable(exc) from exc


@router.post("/{job_id}/retry", response_model=JobEnqueueRead)
def retry_failed_job(job_id: str, queue_name: str = Query(default=INGESTION_QUEUE)) -> JobEnqueueRead:
    try:
        queue: Queue = get_queue(queue_name)
        registry = FailedJobRegistry(queue=queue)
        if job_id not in registry.get_job_ids():
            raise HTTPException(status_code=404, detail="Failed job not found in queue")
        registry.requeue(job_id)
        job = Job.fetch(job_id, connection=queue.connection)
        return JobEnqueueRead(job_id=job.id, queue=queue.name, status=job.get_status(refresh=True))
    except RedisError as exc:
        raise _queue_unavailable(exc) from exc
