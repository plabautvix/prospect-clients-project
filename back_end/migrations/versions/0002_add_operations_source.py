"""add operations.source

Tells the frontend which deactivate endpoint to call, so stopping an operation
still works after a page reload. Existing rows are all Google Maps operations,
hence the server default.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "operations",
        sa.Column(
            "source",
            sa.String(length=20),
            nullable=False,
            server_default="maps",
        ),
    )


def downgrade() -> None:
    op.drop_column("operations", "source")
