"""add password_reset_tokens

"Esqueci a senha" e-mails a link with a random token. Only its SHA-256 is
stored, with an expiry and the moment it was used, so each link works once.

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("id_token", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "id_person", sa.Integer(), sa.ForeignKey("user.id_person"), nullable=False
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_password_reset_tokens_id_person", "password_reset_tokens", ["id_person"]
    )


def downgrade() -> None:
    op.drop_index("ix_password_reset_tokens_id_person", "password_reset_tokens")
    op.drop_table("password_reset_tokens")
