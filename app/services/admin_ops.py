from collections import Counter, defaultdict
from time import perf_counter

import httpx
from redis.exceptions import RedisError
from rq.registry import FailedJobRegistry, StartedJobRegistry
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.redis import get_redis_connection
from app.db.models import (
    AdminAuditLog,
    IngestionBatch,
    IngestionBatchStatus,
    Notification,
    Opportunity,
    OpportunitySource,
    ProfileOpportunityStatus,
    ProfileOpportunityStatusValue,
    ResearcherProfile,
)
from app.schemas.admin import AdminAnalyticsRead, AdminHealthCheckRead, SourceQualityRead
from app.services.serialization import unpack_list
from app.workers.queues import QUEUE_NAMES, get_queue


def log_admin_action(db: Session, actor_user_id: int | None, action: str, entity_type: str, entity_id: int | None, message: str) -> AdminAuditLog:
    entry = AdminAuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        message=message,
    )
    db.add(entry)
    db.flush()
    return entry


def build_admin_analytics(db: Session) -> AdminAnalyticsRead:
    opportunities = db.query(Opportunity).all()
    statuses = db.query(ProfileOpportunityStatus).all()
    saved_counts = Counter(
        status.opportunity_id
        for status in statuses
        if status.status in {ProfileOpportunityStatusValue.saved, ProfileOpportunityStatusValue.planned, ProfileOpportunityStatusValue.applied}
    )
    titles_by_id = {opportunity.id: opportunity.title for opportunity in opportunities}
    most_saved = [
        {"opportunity_id": opportunity_id, "title": titles_by_id.get(opportunity_id, ""), "count": count}
        for opportunity_id, count in saved_counts.most_common(10)
    ]

    discipline_counter: Counter[str] = Counter()
    for opportunity in opportunities:
        discipline_counter.update(unpack_list(opportunity.disciplines))

    source_groups: dict[str, list[Opportunity]] = defaultdict(list)
    for opportunity in opportunities:
        source_groups[opportunity.source].append(opportunity)

    source_quality = [
        SourceQualityRead(
            source=source,
            opportunity_count=len(items),
            missing_deadline_count=sum(1 for item in items if item.deadline is None),
            missing_summary_count=sum(1 for item in items if not item.summary),
            saved_count=sum(saved_counts.get(item.id, 0) for item in items),
        )
        for source, items in sorted(source_groups.items())
    ]

    return AdminAnalyticsRead(
        total_opportunities=len(opportunities),
        total_profiles=db.query(ResearcherProfile).count(),
        total_notifications=db.query(Notification).count(),
        most_saved_opportunities=most_saved,
        most_common_disciplines=[
            {"field": field, "count": count} for field, count in discipline_counter.most_common(10)
        ],
        source_quality=source_quality,
        match_score_distribution=_build_match_score_distribution(db),
    )


def build_admin_health(db: Session) -> list[AdminHealthCheckRead]:
    return [
        _check_database(db),
        _check_redis(),
        _check_elasticsearch(),
        _check_worker_queues(),
        _check_email_provider(),
    ]


def duplicate_groups(db: Session) -> list[list[Opportunity]]:
    opportunities = db.query(Opportunity).all()
    by_url: dict[str, list[Opportunity]] = defaultdict(list)
    by_title_source: dict[str, list[Opportunity]] = defaultdict(list)
    for opportunity in opportunities:
        by_url[opportunity.url.lower()].append(opportunity)
        by_title_source[f"{opportunity.title.lower()}::{opportunity.source.lower()}"].append(opportunity)
    groups = []
    seen_ids: set[int] = set()
    for collection in list(by_url.values()) + list(by_title_source.values()):
        group = [item for item in collection if item.id not in seen_ids]
        if len(group) > 1:
            groups.append(group)
            seen_ids.update(item.id for item in group)
    return groups


def _build_match_score_distribution(db: Session) -> dict[str, int]:
    from app.services.recommendations import RecommendationQuery, list_recommendations

    buckets = {"0-25": 0, "26-50": 0, "51-75": 0, "76-100": 0}
    profiles = db.query(ResearcherProfile).limit(25).all()
    query = RecommendationQuery(include_ignored=True, limit=50, offset=0, active_only=True)
    for profile in profiles:
        try:
            for item in list_recommendations(db, profile, query):
                score = item.match_score
                if score <= 25:
                    buckets["0-25"] += 1
                elif score <= 50:
                    buckets["26-50"] += 1
                elif score <= 75:
                    buckets["51-75"] += 1
                else:
                    buckets["76-100"] += 1
        except Exception:
            db.rollback()
    return buckets


def _timed_check(name: str, operation) -> AdminHealthCheckRead:
    started_at = perf_counter()
    try:
        detail = operation()
        return AdminHealthCheckRead(
            name=name,
            status="healthy",
            detail=detail,
            latency_ms=round((perf_counter() - started_at) * 1000, 2),
        )
    except Exception as exc:
        return AdminHealthCheckRead(
            name=name,
            status="degraded",
            detail=str(exc),
            latency_ms=round((perf_counter() - started_at) * 1000, 2),
        )


def _check_database(db: Session) -> AdminHealthCheckRead:
    return _timed_check("PostgreSQL / database", lambda: _database_detail(db))


def _database_detail(db: Session) -> str:
    db.execute(text("SELECT 1")).scalar_one()
    return f"{db.bind.dialect.name if db.bind else 'database'} connection OK"


def _check_redis() -> AdminHealthCheckRead:
    return _timed_check("Redis", lambda: "Redis ping OK" if get_redis_connection().ping() else "Redis ping failed")


def _check_elasticsearch() -> AdminHealthCheckRead:
    if not settings.elasticsearch_enabled:
        return AdminHealthCheckRead(name="Elasticsearch", status="disabled", detail="Elasticsearch is disabled in settings")
    return _timed_check("Elasticsearch", _elasticsearch_detail)


def _elasticsearch_detail() -> str:
    response = httpx.get(f"{settings.elasticsearch_url.rstrip('/')}/_cluster/health", timeout=3)
    response.raise_for_status()
    payload = response.json()
    return f"cluster={payload.get('cluster_name', 'unknown')} status={payload.get('status', 'unknown')}"


def _check_worker_queues() -> AdminHealthCheckRead:
    def detail() -> str:
        queue_summaries = []
        for name in QUEUE_NAMES:
            queue = get_queue(name)
            failed = len(FailedJobRegistry(queue=queue))
            started = len(StartedJobRegistry(queue=queue))
            queue_summaries.append(f"{name}: queued={queue.count}, started={started}, failed={failed}")
        return "; ".join(queue_summaries)

    try:
        return _timed_check("Worker queues", detail)
    except RedisError as exc:
        return AdminHealthCheckRead(name="Worker queues", status="degraded", detail=str(exc), latency_ms=None)


def _check_email_provider() -> AdminHealthCheckRead:
    if settings.email_provider.lower().strip() == "smtp":
        configured = bool(settings.smtp_host and settings.smtp_port and settings.email_from)
        return AdminHealthCheckRead(
            name="Email provider",
            status="healthy" if configured else "degraded",
            detail=f"SMTP configured for {settings.smtp_host}:{settings.smtp_port}" if configured else "SMTP settings are incomplete",
        )
    return AdminHealthCheckRead(name="Email provider", status="healthy", detail="Console email provider is active")
