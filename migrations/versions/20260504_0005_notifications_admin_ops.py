"""notifications and admin operations

Revision ID: 20260504_0005
Revises: 20260504_0004
Create Date: 2026-05-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260504_0005"
down_revision: Union[str, None] = "20260504_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


notification_status = sa.Enum("pending", "sent", "skipped", "read", name="notificationstatus")
notification_type = sa.Enum("deadline_reminder", "weekly_digest", "high_match_alert", name="notificationtype")


def upgrade() -> None:
    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("email_enabled", sa.Boolean(), nullable=False),
        sa.Column("deadline_reminders_enabled", sa.Boolean(), nullable=False),
        sa.Column("weekly_digest_enabled", sa.Boolean(), nullable=False),
        sa.Column("high_match_alerts_enabled", sa.Boolean(), nullable=False),
        sa.Column("min_alert_score", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_notification_preferences_user"),
    )
    op.create_index(op.f("ix_notification_preferences_id"), "notification_preferences", ["id"], unique=False)
    op.create_index(op.f("ix_notification_preferences_user_id"), "notification_preferences", ["user_id"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("profile_id", sa.Integer(), nullable=True),
        sa.Column("opportunity_id", sa.Integer(), nullable=True),
        sa.Column("reminder_id", sa.Integer(), nullable=True),
        sa.Column("notification_type", notification_type, nullable=False),
        sa.Column("channel", sa.String(length=40), nullable=False),
        sa.Column("subject", sa.String(length=300), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", notification_status, nullable=False),
        sa.Column("skip_reason", sa.String(length=200), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.ForeignKeyConstraint(["profile_id"], ["researcher_profiles.id"]),
        sa.ForeignKeyConstraint(["reminder_id"], ["opportunity_reminders.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("id", "user_id", "profile_id", "opportunity_id", "reminder_id", "notification_type", "channel", "status", "created_at"):
        op.create_index(op.f(f"ix_notifications_{column}"), "notifications", [column], unique=False)

    op.create_table(
        "admin_audit_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("id", "actor_user_id", "action", "entity_type", "entity_id", "created_at"):
        op.create_index(op.f(f"ix_admin_audit_log_{column}"), "admin_audit_log", [column], unique=False)


def downgrade() -> None:
    op.drop_table("admin_audit_log")
    op.drop_table("notifications")
    op.drop_table("notification_preferences")
