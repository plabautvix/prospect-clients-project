from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import Integer, String

from .base import Base


class Campaign(Base):
    """One batch send over a single channel, created by a user.

    status: running, paused, cancelled or completed.
    """

    __tablename__ = "campaigns"

    id_campaign: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_user: Mapped[int] = mapped_column(ForeignKey("user.id_person"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    template: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class OutboundMessage(Base):
    """A message waiting to be sent, or the record that it was.

    This row is the durable copy: whatever goes down, the message is still
    here and is sent once a worker is back.

    status: pending, sending, sent, failed or cancelled. A row in "sending"
    whose locked_until has passed belongs to a worker that died, and is claimed
    again.
    """

    __tablename__ = "outbound_messages"
    __table_args__ = (
        UniqueConstraint("id_campaign", "id_lead", name="uq_message_campaign_lead"),
        Index("ix_outbound_channel_status", "channel", "status"),
    )

    id_message: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_campaign: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id_campaign"), nullable=False
    )
    id_lead: Mapped[int] = mapped_column(ForeignKey("leads.id_lead"), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    # Normalized phone (55DDXXXXXXXXX) or Instagram handle without the @.
    recipient: Mapped[str] = mapped_column(String(100), nullable=False)
    # Rendered when the campaign is created, so what goes out is exactly what
    # the user previewed.
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SenderChannel(Base):
    """State of the one sender account behind a channel.

    Pacing lives here and not in the worker's memory, so a restart cannot
    reset it and fire a fresh chunk right away.

    health: unknown, ok, disconnected or blocked, as last reported by the worker.
    """

    __tablename__ = "sender_channels"

    channel: Mapped[str] = mapped_column(String(20), primary_key=True)
    next_allowed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sent_in_chunk: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    paused_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    health: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    health_detail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Data URL of the WhatsApp pairing QR code while the account is disconnected.
    qr_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Set when the user asks for a fresh QR code. The backend cannot reach the
    # gateway, so the worker picks this up on its next health report.
    reconnect_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
