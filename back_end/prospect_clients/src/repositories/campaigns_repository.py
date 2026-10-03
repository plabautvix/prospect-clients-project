from datetime import datetime

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import Session

from prospect_clients.src.models.tables.campaigns import (
    Campaign,
    OutboundMessage,
    SenderChannel,
)
from prospect_clients.src.models.tables.leads import Leads
from prospect_clients.src.repositories.leads_repository import LeadsRepository

# Statuses that still count as "this person is being, or was, contacted".
# A failed or cancelled message does not stop a later campaign from trying.
CONTACTED = ("pending", "sending", "sent")


class CampaignsRepository:
    def __init__(self, db: Session):
        self.db = db
        self.leads = LeadsRepository(db)

    # ─── Campaigns ───────────────────────────────────────────────────────────

    def contacted_recipients(
        self, user_id: int, channel: str, recipients: list[str]
    ) -> set[str]:
        """Which of these recipients this user already reached on the channel."""
        if not recipients:
            return set()
        rows = self.db.execute(
            select(OutboundMessage.recipient)
            .join(Campaign, Campaign.id_campaign == OutboundMessage.id_campaign)
            .where(Campaign.id_user == user_id)
            .where(OutboundMessage.channel == channel)
            .where(OutboundMessage.status.in_(CONTACTED))
            .where(OutboundMessage.recipient.in_(recipients))
            .distinct()
        )
        return {row[0] for row in rows}

    def create_campaign(
        self, campaign: Campaign, messages: list[OutboundMessage]
    ) -> Campaign:
        """Campaign and messages in one transaction: all of it or nothing."""
        self.db.add(campaign)
        self.db.flush()
        for message in messages:
            message.id_campaign = campaign.id_campaign
        self.db.add_all(messages)
        self.db.commit()
        self.db.refresh(campaign)
        return campaign

    def get_campaign(self, campaign_id: int, user_id: int) -> Campaign | None:
        return (
            self.db.query(Campaign)
            .filter(Campaign.id_campaign == campaign_id)
            .filter(Campaign.id_user == user_id)
            .first()
        )

    def list_campaigns(self, user_id: int) -> list[Campaign]:
        return (
            self.db.query(Campaign)
            .filter(Campaign.id_user == user_id)
            .order_by(Campaign.id_campaign.desc())
            .all()
        )

    def status_counts(self, campaign_ids: list[int]) -> dict[int, dict[str, int]]:
        if not campaign_ids:
            return {}
        rows = self.db.execute(
            select(
                OutboundMessage.id_campaign,
                OutboundMessage.status,
                func.count(OutboundMessage.id_message),
            )
            .where(OutboundMessage.id_campaign.in_(campaign_ids))
            .group_by(OutboundMessage.id_campaign, OutboundMessage.status)
        )
        counts: dict[int, dict[str, int]] = {cid: {} for cid in campaign_ids}
        for campaign_id, status, total in rows:
            counts[campaign_id][status] = total
        return counts

    def set_campaign_status(self, campaign: Campaign, status: str) -> Campaign:
        campaign.status = status
        self.db.commit()
        self.db.refresh(campaign)
        return campaign

    def cancel_waiting_messages(self, campaign_id: int, now: datetime) -> int:
        """Cancel what has not gone out.

        A message in flight, with a live lease, is left alone: its worker is
        sending it right now and will report the outcome.
        """
        result = self.db.execute(
            update(OutboundMessage)
            .where(OutboundMessage.id_campaign == campaign_id)
            .where(
                or_(
                    OutboundMessage.status == "pending",
                    and_(
                        OutboundMessage.status == "sending",
                        OutboundMessage.locked_until <= now,
                    ),
                )
            )
            .values(status="cancelled", locked_until=None)
        )
        self.db.commit()
        return result.rowcount

    def complete_if_done(self, campaign_id: int) -> None:
        """Mark a running campaign completed once nothing is left to send."""
        remaining = self.db.scalar(
            select(func.count(OutboundMessage.id_message))
            .where(OutboundMessage.id_campaign == campaign_id)
            .where(OutboundMessage.status.in_(("pending", "sending")))
        )
        if remaining == 0:
            self.db.execute(
                update(Campaign)
                .where(Campaign.id_campaign == campaign_id)
                .where(Campaign.status == "running")
                .values(status="completed")
            )
            self.db.commit()

    def list_messages(
        self,
        campaign_id: int,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[tuple[OutboundMessage, str]], int]:
        query = (
            self.db.query(OutboundMessage, Leads.nome)
            .join(Leads, Leads.id_lead == OutboundMessage.id_lead)
            .filter(OutboundMessage.id_campaign == campaign_id)
        )
        if status:
            query = query.filter(OutboundMessage.status == status)
        total = query.count()
        items = (
            query.order_by(OutboundMessage.id_message)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    # ─── Sending (service side) ──────────────────────────────────────────────

    def get_channel(self, channel: str) -> SenderChannel:
        state = self.db.get(SenderChannel, channel)
        if state is None:
            state = SenderChannel(channel=channel, sent_in_chunk=0, health="unknown")
            self.db.add(state)
            self.db.commit()
            self.db.refresh(state)
        return state

    def save(self) -> None:
        self.db.commit()

    def sent_since(self, channel: str, since: datetime) -> int:
        return self.db.scalar(
            select(func.count(OutboundMessage.id_message))
            .where(OutboundMessage.channel == channel)
            .where(OutboundMessage.status == "sent")
            .where(OutboundMessage.sent_at >= since)
        )

    def queued(self, channel: str) -> int:
        return self.db.scalar(
            select(func.count(OutboundMessage.id_message))
            .join(Campaign, Campaign.id_campaign == OutboundMessage.id_campaign)
            .where(OutboundMessage.channel == channel)
            .where(OutboundMessage.status.in_(("pending", "sending")))
            .where(Campaign.status == "running")
        )

    def live_lease_until(self, channel: str, now: datetime) -> datetime | None:
        """End of the lease of a message being sent right now, if any."""
        return self.db.scalar(
            select(func.max(OutboundMessage.locked_until))
            .where(OutboundMessage.channel == channel)
            .where(OutboundMessage.status == "sending")
            .where(OutboundMessage.locked_until > now)
        )

    def claim_next(
        self, channel: str, now: datetime, lease_until: datetime
    ) -> OutboundMessage | None:
        """Take the oldest sendable message and lease it, atomically.

        A single UPDATE ... RETURNING, so two callers can never take the same
        row. Sendable means pending and due, or stuck in sending with an
        expired lease, which is a worker that died mid-send. Only running
        campaigns are served, oldest message first, so campaigns go out in
        the order they were created.

        On Postgres this is where FOR UPDATE SKIP LOCKED would go.
        """
        candidate = (
            select(OutboundMessage.id_message)
            .join(Campaign, Campaign.id_campaign == OutboundMessage.id_campaign)
            .where(OutboundMessage.channel == channel)
            .where(Campaign.status == "running")
            .where(
                or_(
                    and_(
                        OutboundMessage.status == "pending",
                        or_(
                            OutboundMessage.next_attempt_at.is_(None),
                            OutboundMessage.next_attempt_at <= now,
                        ),
                    ),
                    and_(
                        OutboundMessage.status == "sending",
                        OutboundMessage.locked_until <= now,
                    ),
                )
            )
            .order_by(OutboundMessage.id_message)
            .limit(1)
            .scalar_subquery()
        )
        claimed_id = self.db.execute(
            update(OutboundMessage)
            .where(OutboundMessage.id_message == candidate)
            .values(
                status="sending",
                locked_until=lease_until,
                attempts=OutboundMessage.attempts + 1,
            )
            .returning(OutboundMessage.id_message)
            .execution_options(synchronize_session=False)
        ).scalar_one_or_none()
        self.db.commit()

        if claimed_id is None:
            return None
        return self.get_message(claimed_id)

    def get_message(self, message_id: int) -> OutboundMessage | None:
        message = self.db.get(OutboundMessage, message_id)
        if message is not None:
            # The claim bypassed the session, so drop any stale copy.
            self.db.refresh(message)
        return message
