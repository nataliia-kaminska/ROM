from datetime import date, datetime
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CareerStage(str, Enum):
    bachelor = "bachelor"
    master = "master"
    phd = "phd"
    postdoc = "postdoc"
    early_career = "early_career"
    senior = "senior"


class OpportunityType(str, Enum):
    grant = "grant"
    exchange = "exchange"
    fellowship = "fellowship"
    internship = "internship"
    research_position = "research_position"
    training = "training"


class ProfileOpportunityStatusValue(str, Enum):
    saved = "saved"
    ignored = "ignored"
    planned = "planned"
    applied = "applied"
    rejected = "rejected"
    accepted = "accepted"


class ReminderStatus(str, Enum):
    pending = "pending"
    completed = "completed"


class IngestionBatchStatus(str, Enum):
    dry_run = "dry_run"
    success = "success"
    failed = "failed"


class UserRole(str, Enum):
    researcher = "researcher"
    admin = "admin"


class NotificationStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    skipped = "skipped"
    read = "read"


class NotificationType(str, Enum):
    deadline_reminder = "deadline_reminder"
    weekly_digest = "weekly_digest"
    high_match_alert = "high_match_alert"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(500))
    full_name: Mapped[str] = mapped_column(String(200), default="")
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole), default=UserRole.researcher, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ResearcherProfile(Base):
    __tablename__ = "researcher_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200), index=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True, index=True)
    career_stage: Mapped[CareerStage] = mapped_column(SqlEnum(CareerStage), index=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    disciplines: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[str] = mapped_column(Text, default="")
    preferred_countries: Mapped[str] = mapped_column(Text, default="")
    orcid_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    google_scholar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ResearcherProfileDetails(Base):
    __tablename__ = "researcher_profile_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("researcher_profiles.id"), unique=True, index=True)
    research_summary: Mapped[str] = mapped_column(Text, default="")
    publications: Mapped[str] = mapped_column(Text, default="")
    degrees: Mapped[str] = mapped_column(Text, default="")
    languages: Mapped[str] = mapped_column(Text, default="")
    funding_interests: Mapped[str] = mapped_column(Text, default="")
    unavailable_countries: Mapped[str] = mapped_column(Text, default="")
    preferred_opportunity_types: Mapped[str] = mapped_column(Text, default="")
    min_duration_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_duration_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    profile_embedding: Mapped[str] = mapped_column(Text, default="")
    embedding_model: Mapped[str] = mapped_column(String(200), default="")
    embedding_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class Opportunity(Base):
    __tablename__ = "opportunities"
    __table_args__ = (UniqueConstraint("url", name="uq_opportunity_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    opportunity_type: Mapped[OpportunityType] = mapped_column(SqlEnum(OpportunityType), index=True)
    source: Mapped[str] = mapped_column(String(120), index=True)
    url: Mapped[str] = mapped_column(String(800), index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    eligibility: Mapped[str] = mapped_column(Text, default="")
    disciplines: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[str] = mapped_column(Text, default="")
    countries: Mapped[str] = mapped_column(Text, default="")
    career_stages: Mapped[str] = mapped_column(Text, default="")
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    opportunity_embedding: Mapped[str] = mapped_column(Text, default="")
    embedding_model: Mapped[str] = mapped_column(String(200), default="")
    embedding_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class OpportunitySource(Base):
    __tablename__ = "opportunity_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    base_url: Mapped[str | None] = mapped_column(String(800), nullable=True)
    source_type: Mapped[str] = mapped_column(String(80), default="curated")
    notes: Mapped[str] = mapped_column(Text, default="")
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class IngestionBatch(Base):
    __tablename__ = "ingestion_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_name: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[IngestionBatchStatus] = mapped_column(SqlEnum(IngestionBatchStatus), index=True)
    imported_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    query: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class IngestionError(Base):
    __tablename__ = "ingestion_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("ingestion_batches.id"), index=True)
    message: Mapped[str] = mapped_column(Text)
    raw_payload: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ProfileOpportunityStatus(Base):
    __tablename__ = "profile_opportunity_statuses"
    __table_args__ = (UniqueConstraint("profile_id", "opportunity_id", name="uq_profile_opportunity_status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("researcher_profiles.id"), index=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), index=True)
    status: Mapped[ProfileOpportunityStatusValue] = mapped_column(SqlEnum(ProfileOpportunityStatusValue), index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class OpportunityReminder(Base):
    __tablename__ = "opportunity_reminders"
    __table_args__ = (UniqueConstraint("profile_id", "opportunity_id", "remind_on", name="uq_profile_opportunity_reminder_day"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("researcher_profiles.id"), index=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id"), index=True)
    remind_on: Mapped[date] = mapped_column(Date, index=True)
    message: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[ReminderStatus] = mapped_column(SqlEnum(ReminderStatus), default=ReminderStatus.pending, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


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


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(120), index=True)
    entity_type: Mapped[str] = mapped_column(String(120), index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
