"""add refresh token metadata

Revision ID: 20260517_0011
Revises: 20260517_0010
Create Date: 2026-05-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260517_0011"
down_revision: Union[str, None] = "20260517_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("refresh_token_hash", sa.String(length=128), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("refresh_token_expires_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("refresh_token_expires_at")
        batch_op.drop_column("refresh_token_hash")
