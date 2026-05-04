from datetime import datetime

from pydantic import BaseModel

from app.schemas.ingestion_audit import IngestionBatchRead, OpportunitySourceRead
from app.schemas.opportunities import OpportunityRead


class AdminAuditLogRead(BaseModel):
    id: int
    actor_user_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DuplicateOpportunityGroup(BaseModel):
    key: str
    opportunities: list[OpportunityRead]


class DuplicateMergeRequest(BaseModel):
    target_opportunity_id: int
    duplicate_opportunity_ids: list[int]


class SourceQualityRead(BaseModel):
    source: str
    opportunity_count: int
    missing_deadline_count: int
    missing_summary_count: int
    saved_count: int


class AdminAnalyticsRead(BaseModel):
    total_opportunities: int
    total_profiles: int
    total_notifications: int
    most_saved_opportunities: list[dict]
    most_common_disciplines: list[dict]
    source_quality: list[SourceQualityRead]
    match_score_distribution: dict[str, int]


class AdminDashboardRead(BaseModel):
    sources: list[OpportunitySourceRead]
    recent_batches: list[IngestionBatchRead]
    failed_batches: list[IngestionBatchRead]
    analytics: AdminAnalyticsRead
