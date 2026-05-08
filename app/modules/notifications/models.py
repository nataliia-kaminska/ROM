from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.domain.enums import NotificationStatus, NotificationType


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    __table_args__ = (UniqueConstraint("user_id", name="uq_notification_preferences_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    deadline_reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    weekly_digest_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    high_match_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    min_alert_score: Mapped[int] = mapped_column(Integer, default=80)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("researcher_profiles.id"), nullable=True, index=True)
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id"), nullable=True, index=True)
    reminder_id: Mapped[int | None] = mapped_column(ForeignKey("opportunity_reminders.id"), nullable=True, index=True)
    notification_type: Mapped[NotificationType] = mapped_column(SqlEnum(NotificationType), index=True)
    channel: Mapped[str] = mapped_column(String(40), default="email", index=True)
    recipient: Mapped[str] = mapped_column(String(320), default="")
    provider: Mapped[str] = mapped_column(String(80), default="")
    provider_message_id: Mapped[str] = mapped_column(String(200), default="")
    delivery_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str] = mapped_column(Text, default="")
    subject: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[NotificationStatus] = mapped_column(SqlEnum(NotificationStatus), default=NotificationStatus.pending, index=True)
    skip_reason: Mapped[str] = mapped_column(String(200), default="")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
