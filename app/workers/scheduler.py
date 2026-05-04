import logging
import time

from rq import Retry

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.redis import get_redis_connection
from app.workers.jobs import ingest_grants_gov_job, scan_due_reminders_job, send_high_match_alerts_job, send_weekly_digest_job
from app.workers.queues import INGESTION_QUEUE, REMINDERS_QUEUE, get_queue


logger = logging.getLogger(__name__)


def enqueue_recurring_jobs() -> None:
    redis = get_redis_connection()
    ingestion_queue = get_queue(INGESTION_QUEUE)
    reminders_queue = get_queue(REMINDERS_QUEUE)

    for keyword in settings.scheduled_grants_gov_keywords:
        key = f"scheduler:grants-gov:{keyword}"
        if redis.set(key, "1", ex=settings.source_sync_interval_seconds, nx=True):
            ingestion_queue.enqueue(
                ingest_grants_gov_job,
                kwargs={"keyword": keyword, "limit": settings.source_sync_limit, "import_results": True},
                retry=Retry(max=3, interval=[60, 300, 900]),
                job_timeout="15m",
                description=f"Recurring Grants.gov sync for {keyword}",
            )
            logger.info("enqueued recurring grants.gov sync keyword=%s", keyword)

    if redis.set("scheduler:reminders:scan", "1", ex=settings.reminder_scan_interval_seconds, nx=True):
        reminders_queue.enqueue(
            scan_due_reminders_job,
            retry=Retry(max=3, interval=[60, 300, 900]),
            job_timeout="5m",
            description="Scan due opportunity reminders",
        )
        logger.info("enqueued due reminder scan")

    if redis.set("scheduler:notifications:weekly-digest", "1", ex=settings.weekly_digest_interval_seconds, nx=True):
        reminders_queue.enqueue(
            send_weekly_digest_job,
            retry=Retry(max=3, interval=[60, 300, 900]),
            job_timeout="10m",
            description="Send weekly recommendation digest",
        )
        logger.info("enqueued weekly recommendation digest")

    if redis.set("scheduler:notifications:high-match-alerts", "1", ex=settings.high_match_alert_interval_seconds, nx=True):
        reminders_queue.enqueue(
            send_high_match_alerts_job,
            retry=Retry(max=3, interval=[60, 300, 900]),
            job_timeout="10m",
            description="Send high-match opportunity alerts",
        )
        logger.info("enqueued high-match alerts")


def main() -> None:
    configure_logging()
    while True:
        enqueue_recurring_jobs()
        time.sleep(settings.scheduler_tick_seconds)


if __name__ == "__main__":
    main()
