"""add sender_channels.needs_code and verification_code

Instagram may ask for a code (e-mail or SMS) when the sender account logs in
from a new device. The worker reports that it is waiting for one, the user
types it in the app, and the worker gets it with its next health report. The
code is cleared as soon as it is handed over.

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("sender_channels") as batch:
        batch.add_column(
            sa.Column(
                "needs_code", sa.Boolean(), nullable=False, server_default=sa.false()
            )
        )
        batch.add_column(sa.Column("verification_code", sa.String(20), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("sender_channels") as batch:
        batch.drop_column("verification_code")
        batch.drop_column("needs_code")
