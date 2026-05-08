from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Text, UniqueConstraint, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.domain.enums import ProfileOpportunityStatusValue, ReminderStatus


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
