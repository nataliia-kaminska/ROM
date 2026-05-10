"""add user email verification

Revision ID: 20260510_0009
Revises: 20260504_0008
Create Date: 2026-05-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260510_0009"
down_revision: Union[str, None] = "20260504_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("email_verification_token_hash", sa.String(length=128), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("email_verification_expires_at", sa.DateTime(), nullable=True))
        batch_op.create_index("ix_users_email_verified", ["email_verified"])
    op.execute("UPDATE users SET email_verified = TRUE")


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_email_verified")
        batch_op.drop_column("email_verification_expires_at")
        batch_op.drop_column("email_verification_token_hash")
        batch_op.drop_column("email_verified")
