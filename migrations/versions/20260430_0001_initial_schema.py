"""initial schema

Revision ID: 20260430_0001
Revises:
Create Date: 2026-04-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260430_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


career_stage = sa.Enum(
    "bachelor",
    "master",
    "phd",
    "postdoc",
    "early_career",
    "senior",
    name="careerstage",
)
opportunity_type = sa.Enum(
    "grant",
    "exchange",
    "fellowship",
    "internship",
    "research_position",
    "training",
    name="opportunitytype",
)
profile_status = sa.Enum(
    "saved",
    "ignored",
    "planned",
    "applied",
    "rejected",
    "accepted",
    name="profileopportunitystatusvalue",
)
reminder_status = sa.Enum("pending", "completed", name="reminderstatus")


def upgrade() -> None:
    op.create_table(
        "researcher_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("career_stage", career_stage, nullable=False),
        sa.Column("country", sa.String(length=120), nullable=True),
        sa.Column("disciplines", sa.Text(), nullable=False),
        sa.Column("keywords", sa.Text(), nullable=False),
        sa.Column("preferred_countries", sa.Text(), nullable=False),
        sa.Column("orcid_id", sa.String(length=64), nullable=True),
        sa.Column("google_scholar_url", sa.String(length=500), nullable=True),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_researcher_profiles_email"), "researcher_profiles", ["email"], unique=False)
    op.create_index(op.f("ix_researcher_profiles_full_name"), "researcher_profiles", ["full_name"], unique=False)
    op.create_index(op.f("ix_researcher_profiles_id"), "researcher_profiles", ["id"], unique=False)
    op.create_index(op.f("ix_researcher_profiles_career_stage"), "researcher_profiles", ["career_stage"], unique=False)

    op.create_table(
        "opportunities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("opportunity_type", opportunity_type, nullable=False),
        sa.Column("source", sa.String(length=120), nullable=False),
        sa.Column("url", sa.String(length=800), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("eligibility", sa.Text(), nullable=False),
        sa.Column("disciplines", sa.Text(), nullable=False),
        sa.Column("keywords", sa.Text(), nullable=False),
        sa.Column("countries", sa.Text(), nullable=False),
        sa.Column("career_stages", sa.Text(), nullable=False),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url", name="uq_opportunity_url"),
    )
    op.create_index(op.f("ix_opportunities_deadline"), "opportunities", ["deadline"], unique=False)
    op.create_index(op.f("ix_opportunities_id"), "opportunities", ["id"], unique=False)
    op.create_index(op.f("ix_opportunities_opportunity_type"), "opportunities", ["opportunity_type"], unique=False)
    op.create_index(op.f("ix_opportunities_source"), "opportunities", ["source"], unique=False)
    op.create_index(op.f("ix_opportunities_title"), "opportunities", ["title"], unique=False)
    op.create_index(op.f("ix_opportunities_url"), "opportunities", ["url"], unique=False)

    op.create_table(
        "researcher_profile_details",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("research_summary", sa.Text(), nullable=False),
        sa.Column("publications", sa.Text(), nullable=False),
        sa.Column("degrees", sa.Text(), nullable=False),
        sa.Column("languages", sa.Text(), nullable=False),
        sa.Column("funding_interests", sa.Text(), nullable=False),
        sa.Column("unavailable_countries", sa.Text(), nullable=False),
        sa.Column("preferred_opportunity_types", sa.Text(), nullable=False),
        sa.Column("min_duration_months", sa.Integer(), nullable=True),
        sa.Column("max_duration_months", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["researcher_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_researcher_profile_details_id"), "researcher_profile_details", ["id"], unique=False)
    op.create_index(op.f("ix_researcher_profile_details_profile_id"), "researcher_profile_details", ["profile_id"], unique=True)

    op.create_table(
        "profile_opportunity_statuses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("opportunity_id", sa.Integer(), nullable=False),
        sa.Column("status", profile_status, nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["researcher_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "opportunity_id", name="uq_profile_opportunity_status"),
    )
    op.create_index(op.f("ix_profile_opportunity_statuses_id"), "profile_opportunity_statuses", ["id"], unique=False)
    op.create_index(op.f("ix_profile_opportunity_statuses_opportunity_id"), "profile_opportunity_statuses", ["opportunity_id"], unique=False)
    op.create_index(op.f("ix_profile_opportunity_statuses_profile_id"), "profile_opportunity_statuses", ["profile_id"], unique=False)
    op.create_index(op.f("ix_profile_opportunity_statuses_status"), "profile_opportunity_statuses", ["status"], unique=False)

    op.create_table(
        "opportunity_reminders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("profile_id", sa.Integer(), nullable=False),
        sa.Column("opportunity_id", sa.Integer(), nullable=False),
        sa.Column("remind_on", sa.Date(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", reminder_status, nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["researcher_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "opportunity_id", "remind_on", name="uq_profile_opportunity_reminder_day"),
    )
    op.create_index(op.f("ix_opportunity_reminders_id"), "opportunity_reminders", ["id"], unique=False)
    op.create_index(op.f("ix_opportunity_reminders_opportunity_id"), "opportunity_reminders", ["opportunity_id"], unique=False)
    op.create_index(op.f("ix_opportunity_reminders_profile_id"), "opportunity_reminders", ["profile_id"], unique=False)
    op.create_index(op.f("ix_opportunity_reminders_remind_on"), "opportunity_reminders", ["remind_on"], unique=False)
    op.create_index(op.f("ix_opportunity_reminders_status"), "opportunity_reminders", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("opportunity_reminders")
    op.drop_table("profile_opportunity_statuses")
    op.drop_table("researcher_profile_details")
    op.drop_table("opportunities")
    op.drop_table("researcher_profiles")
