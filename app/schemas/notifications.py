from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models import NotificationStatus, NotificationType


class NotificationPreferenceRead(BaseModel):
    id: int
    user_id: int
    email_enabled: bool
    deadline_reminders_enabled: bool
    weekly_digest_enabled: bool
    high_match_alerts_enabled: bool
    min_alert_score: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationPreferenceUpdate(BaseModel):
    email_enabled: bool = True
    deadline_reminders_enabled: bool = True
    weekly_digest_enabled: bool = True
    high_match_alerts_enabled: bool = True
    min_alert_score: int = Field(default=80, ge=0, le=100)


class NotificationRead(BaseModel):
    id: int
    user_id: int | None
    profile_id: int | None
    opportunity_id: int | None
    reminder_id: int | None
    notification_type: NotificationType
    channel: str
    subject: str
    body: str
    status: NotificationStatus
    skip_reason: str
    sent_at: datetime | None
    read_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
