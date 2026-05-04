"""add extracted opportunity requirements

Revision ID: 20260504_0008
Revises: 20260504_0007
Create Date: 2026-05-04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260504_0008"
down_revision = "20260504_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("opportunities") as batch_op:
        batch_op.add_column(sa.Column("extracted_requirements", sa.Text(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("requirements_confidence", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    with op.batch_alter_table("opportunities") as batch_op:
        batch_op.drop_column("requirements_confidence")
        batch_op.drop_column("extracted_requirements")
