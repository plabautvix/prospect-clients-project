"""initial schema

Baseline of the schema as it was created by Base.metadata.create_all before
Alembic was introduced. A database that predates Alembic already matches this
revision, so stamp it instead of running it:

    alembic stamp 0001

Revision ID: 0001
Revises:
Create Date: 2026-09-20
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id_person", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id_person"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "leads",
        sa.Column("id_lead", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("telefone", sa.String(length=50), nullable=True),
        sa.Column("endereco", sa.String(length=255), nullable=True),
        sa.Column("site", sa.String(length=255), nullable=True),
        sa.Column("foto", sa.String(length=255), nullable=True),
        sa.Column("categoria", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id_lead"),
        sa.UniqueConstraint("nome"),
    )

    op.create_table(
        "operations",
        sa.Column("id_operation", sa.Integer(), nullable=False),
        sa.Column("operation_name", sa.String(), nullable=False),
        sa.Column("search_text", sa.String(), nullable=False),
        sa.Column("message_for_lead", sa.String(), nullable=True),
        sa.Column("status", sa.Integer(), nullable=False),
        sa.Column("id_user", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["id_user"], ["user.id_person"]),
        sa.PrimaryKeyConstraint("id_operation"),
    )

    op.create_table(
        "user_lead_history",
        sa.Column("id_lead_history", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.Column("encontrado_em", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id_lead"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id_person"]),
        sa.PrimaryKeyConstraint("id_lead_history"),
    )


def downgrade() -> None:
    op.drop_table("user_lead_history")
    op.drop_table("operations")
    op.drop_table("leads")
    op.drop_table("user")
