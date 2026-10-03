"""add sender_channels.reconnect_requested_at

Lets the user ask for a fresh WhatsApp QR code from the app. The backend cannot
reach the gateway, on purpose, so the request is stored here and handed to the
worker the next time it reports its health.

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("sender_channels") as batch:
        batch.add_column(
            sa.Column("reconnect_requested_at", sa.DateTime(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("sender_channels") as batch:
        batch.drop_column("reconnect_requested_at")
