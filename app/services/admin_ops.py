from collections import Counter, defaultdict

from sqlalchemy.orm import Session

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
from app.schemas.admin import AdminAnalyticsRead, SourceQualityRead
from app.services.serialization import unpack_list


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
        match_score_distribution={"0-25": 0, "26-50": 0, "51-75": 0, "76-100": 0},
    )


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
