"""add ORCID OAuth user fields

Revision ID: 20260517_0010
Revises: 20260510_0009
Create Date: 2026-05-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260517_0010"
down_revision: Union[str, None] = "20260510_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("auth_provider", sa.String(length=40), nullable=False, server_default="local"))
        batch_op.add_column(sa.Column("orcid_id", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("password_login_enabled", sa.Boolean(), nullable=False, server_default=sa.true()))
        batch_op.create_index("ix_users_auth_provider", ["auth_provider"])
        batch_op.create_index("ix_users_orcid_id", ["orcid_id"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_orcid_id")
        batch_op.drop_index("ix_users_auth_provider")
        batch_op.drop_column("password_login_enabled")
        batch_op.drop_column("orcid_id")
        batch_op.drop_column("auth_provider")
