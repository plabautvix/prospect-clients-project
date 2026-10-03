"""add campaigns, outbound_messages, sender_channels and leads.nao_contatar

Batch sending of WhatsApp and Instagram messages. Every message is stored as a
row before anything is sent, so a crash anywhere never loses one: the worker
that comes back picks it up. See ARCHITECTURE.md, section on sending.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id_campaign", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("id_user", sa.Integer(), sa.ForeignKey("user.id_person"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("template", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "outbound_messages",
        sa.Column("id_message", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "id_campaign",
            sa.Integer(),
            sa.ForeignKey("campaigns.id_campaign"),
            nullable=False,
        ),
        sa.Column("id_lead", sa.Integer(), sa.ForeignKey("leads.id_lead"), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("recipient", sa.String(100), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("id_campaign", "id_lead", name="uq_message_campaign_lead"),
    )
    op.create_index(
        "ix_outbound_channel_status", "outbound_messages", ["channel", "status"]
    )

    op.create_table(
        "sender_channels",
        sa.Column("channel", sa.String(20), primary_key=True),
        sa.Column("next_allowed_at", sa.DateTime(), nullable=True),
        sa.Column("sent_in_chunk", sa.Integer(), nullable=False),
        sa.Column("paused_until", sa.DateTime(), nullable=True),
        sa.Column("health", sa.String(20), nullable=False),
        sa.Column("health_detail", sa.String(500), nullable=True),
        sa.Column("qr_code", sa.Text(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
    )

    with op.batch_alter_table("leads") as batch:
        batch.add_column(
            sa.Column(
                "nao_contatar",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("leads") as batch:
        batch.drop_column("nao_contatar")
    op.drop_table("sender_channels")
    op.drop_index("ix_outbound_channel_status", table_name="outbound_messages")
    op.drop_table("outbound_messages")
    op.drop_table("campaigns")
