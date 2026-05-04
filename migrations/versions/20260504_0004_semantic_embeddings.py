"""semantic embedding storage

Revision ID: 20260504_0004
Revises: 20260501_0003
Create Date: 2026-05-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260504_0004"
down_revision: Union[str, None] = "20260501_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    with op.batch_alter_table("researcher_profile_details") as batch_op:
        batch_op.add_column(sa.Column("profile_embedding", sa.Text(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("embedding_updated_at", sa.DateTime(), nullable=True))

    with op.batch_alter_table("opportunities") as batch_op:
        batch_op.add_column(sa.Column("opportunity_embedding", sa.Text(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("embedding_updated_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("opportunities") as batch_op:
        batch_op.drop_column("embedding_updated_at")
        batch_op.drop_column("opportunity_embedding")

    with op.batch_alter_table("researcher_profile_details") as batch_op:
        batch_op.drop_column("embedding_updated_at")
        batch_op.drop_column("profile_embedding")
