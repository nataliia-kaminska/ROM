"""v1 matching foundation

Revision ID: 20260504_0006
Revises: 20260504_0005
Create Date: 2026-05-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.core.config import settings


revision: str = "20260504_0006"
down_revision: Union[str, None] = "20260504_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    with op.batch_alter_table("researcher_profile_details") as batch_op:
        batch_op.add_column(sa.Column("embedding_model", sa.String(length=200), nullable=False, server_default=""))
    with op.batch_alter_table("opportunities") as batch_op:
        batch_op.add_column(sa.Column("embedding_model", sa.String(length=200), nullable=False, server_default=""))

    if bind.dialect.name == "postgresql":
        vector_dimensions = int(settings.embedding_dimensions)
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.execute(
            "ALTER TABLE researcher_profile_details "
            f"ADD COLUMN IF NOT EXISTS profile_embedding_vector vector({vector_dimensions})"
        )
        op.execute(
            "ALTER TABLE opportunities "
            f"ADD COLUMN IF NOT EXISTS opportunity_embedding_vector vector({vector_dimensions})"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_opportunities_embedding_vector "
            "ON opportunities USING ivfflat (opportunity_embedding_vector vector_cosine_ops)"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_opportunities_embedding_vector")
        op.execute("ALTER TABLE opportunities DROP COLUMN IF EXISTS opportunity_embedding_vector")
        op.execute("ALTER TABLE researcher_profile_details DROP COLUMN IF EXISTS profile_embedding_vector")

    with op.batch_alter_table("opportunities") as batch_op:
        batch_op.drop_column("embedding_model")
    with op.batch_alter_table("researcher_profile_details") as batch_op:
        batch_op.drop_column("embedding_model")
