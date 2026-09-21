"""add leads.origem

Records which service found the lead, so the UI can tell a Google Maps business
from an Instagram profile and filter between them. Every row that exists today
came from the maps scraper, hence the server default.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "leads",
        sa.Column(
            "origem",
            sa.String(length=20),
            nullable=False,
            server_default="maps",
        ),
    )

    # Instagram leads collected before this column existed also defaulted to
    # maps. They are the ones whose name is a handle, which no Google Maps
    # business name ever is.
    op.execute("UPDATE leads SET origem = 'instagram' WHERE nome LIKE '@%'")


def downgrade() -> None:
    op.drop_column("leads", "origem")
