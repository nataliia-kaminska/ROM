"""email delivery metadata

Revision ID: 20260504_0007
Revises: 20260504_0006
Create Date: 2026-05-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260504_0007"
down_revision: Union[str, None] = "20260504_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("notifications") as batch_op:
        batch_op.add_column(sa.Column("recipient", sa.String(length=320), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("provider", sa.String(length=80), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("provider_message_id", sa.String(length=200), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("delivery_attempts", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("last_error", sa.Text(), nullable=False, server_default=""))


def downgrade() -> None:
    with op.batch_alter_table("notifications") as batch_op:
        batch_op.drop_column("last_error")
        batch_op.drop_column("delivery_attempts")
        batch_op.drop_column("provider_message_id")
        batch_op.drop_column("provider")
        batch_op.drop_column("recipient")
