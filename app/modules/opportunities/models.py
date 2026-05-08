from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.domain.enums import OpportunityType


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
    extracted_requirements: Mapped[str] = mapped_column(Text, default="")
    requirements_confidence: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
