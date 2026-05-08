from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.domain.enums import CareerStage


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
