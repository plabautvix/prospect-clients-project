"""add user_lead_history.id_operation

Links each lead back to the operation that found it, so the prospecting screen
can show what a given run collected. The column lives here and not on leads
because leads are deduplicated globally: the same lead can be found by several
operations, and that is a many to many.

Rows written before this column existed keep it null. Their operations simply
show no leads, which is honest: the link was never recorded.

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("user_lead_history") as batch:
        batch.add_column(sa.Column("id_operation", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_history_operation",
            "operations",
            ["id_operation"],
            ["id_operation"],
        )


def downgrade() -> None:
    with op.batch_alter_table("user_lead_history") as batch:
        batch.drop_constraint("fk_history_operation", type_="foreignkey")
        batch.drop_column("id_operation")
