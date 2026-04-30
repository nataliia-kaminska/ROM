"""ingestion audit tables

Revision ID: 20260430_0002
Revises: 20260430_0001
Create Date: 2026-04-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260430_0002"
down_revision: Union[str, None] = "20260430_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ingestion_batch_status = sa.Enum("dry_run", "success", "failed", name="ingestionbatchstatus")


def upgrade() -> None:
    op.create_table(
        "opportunity_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("base_url", sa.String(length=800), nullable=True),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_opportunity_sources_id"), "opportunity_sources", ["id"], unique=False)
    op.create_index(op.f("ix_opportunity_sources_name"), "opportunity_sources", ["name"], unique=True)

    op.create_table(
        "ingestion_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=120), nullable=False),
        sa.Column("status", ingestion_batch_status, nullable=False),
        sa.Column("imported_count", sa.Integer(), nullable=False),
        sa.Column("updated_count", sa.Integer(), nullable=False),
        sa.Column("skipped_count", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("query", sa.String(length=500), nullable=True),
        sa.Column("started_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ingestion_batches_id"), "ingestion_batches", ["id"], unique=False)
    op.create_index(op.f("ix_ingestion_batches_source_name"), "ingestion_batches", ["source_name"], unique=False)
    op.create_index(op.f("ix_ingestion_batches_status"), "ingestion_batches", ["status"], unique=False)

    op.create_table(
        "ingestion_errors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("raw_payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["ingestion_batches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ingestion_errors_batch_id"), "ingestion_errors", ["batch_id"], unique=False)
    op.create_index(op.f("ix_ingestion_errors_id"), "ingestion_errors", ["id"], unique=False)


def downgrade() -> None:
    op.drop_table("ingestion_errors")
    op.drop_table("ingestion_batches")
    op.drop_table("opportunity_sources")

