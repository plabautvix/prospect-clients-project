import math
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from prospect_clients.src.configurations.messaging import (
    IDLE_POLL_SECONDS,
    INSTAGRAM,
    LEASE_SECONDS,
    MAX_ATTEMPTS,
    PACING,
    RETRY_BASE_SECONDS,
    WHATSAPP,
    WORKER_STALE_SECONDS,
)
from prospect_clients.src.models.schemas.campaigns import (
    CampaignCreate,
    CampaignCreated,
    CampaignPreview,
    CampaignResponse,
    CategoryAudience,
    ChannelStatus,
    ClaimedMessage,
    ClaimResponse,
    HealthAck,
    HealthReport,
    MessageResponse,
    MessageSample,
    MessagesPage,
    SendResult,
    SkippedCounts,
    StatusCounts,
)
from prospect_clients.src.models.tables.campaigns import Campaign, OutboundMessage
from prospect_clients.src.models.tables.leads import Leads
from prospect_clients.src.repositories.campaigns_repository import CampaignsRepository
from prospect_clients.src.services.pacing import (
    after_send,
    blocked_until,
    local_day_start,
    utcnow,
)
from prospect_clients.src.utils.phone import instagram_handle, normalize_br_mobile
from prospect_clients.src.utils.template import render_message

CHANNEL_LABELS = {WHATSAPP: "WhatsApp", INSTAGRAM: "Instagram"}
PREVIEW_SAMPLES = 3


def _aware(value: datetime | None) -> datetime | None:
    """Naive UTC from the database, tagged so the browser reads it as UTC."""
    return value.replace(tzinfo=timezone.utc) if value else None


def _seconds_until(now: datetime, moment: datetime) -> int:
    return max(1, math.ceil((moment - now).total_seconds()))


def recipient_for(channel: str, lead: Leads) -> str | None:
    """Where a lead is reached on a channel, or None if it cannot be."""
    if channel == WHATSAPP:
        return normalize_br_mobile(lead.telefone)
    if lead.origem == INSTAGRAM:
        return instagram_handle(lead.nome)
    return None


class CampaignsService:
    def __init__(self, repository: CampaignsRepository):
        self.repository = repository

    # ─── Building a campaign ─────────────────────────────────────────────────

    def _triage(
        self, user_id: int, channel: str, leads: list[Leads]
    ) -> list[tuple[Leads, str | None, str | None]]:
        """For each lead: (lead, recipient, why it is left out or None).

        The single source of who gets a message, so the counts the screen
        shows before a campaign are exactly what the campaign will send.
        """
        # The opt out belongs to the person, not to one row: the same phone or
        # profile can come back as another lead from a later search.
        opted_out = {
            recipient_for(channel, lead)
            for lead in self.repository.leads.get_do_not_contact(user_id)
        }

        triaged: list[list] = []
        seen: set[str] = set()
        for lead in leads:
            recipient = recipient_for(channel, lead)
            if lead.nao_contatar or (recipient and recipient in opted_out):
                reason = "nao_contatar"
            elif recipient is None:
                reason = "sem_contato"
            elif recipient in seen:
                reason = "duplicado"
            else:
                reason = None
                seen.add(recipient)
            triaged.append([lead, recipient, reason])

        contacted = self.repository.contacted_recipients(
            user_id, channel, [r for _, r, why in triaged if why is None]
        )
        for row in triaged:
            if row[2] is None and row[1] in contacted:
                row[2] = "ja_contatado"
        return [tuple(row) for row in triaged]

    def _plan(
        self, user_id: int, data: CampaignCreate
    ) -> tuple[list[tuple[Leads, str]], SkippedCounts]:
        """Which selected leads will get a message, and why the rest will not."""
        filters = data.filters.model_dump() if data.filters else {}
        leads = self.repository.leads.get_all_by_user(
            user_id, lead_ids=data.lead_ids, **filters
        )

        skipped = SkippedCounts()
        eligible: list[tuple[Leads, str]] = []
        for lead, recipient, reason in self._triage(user_id, data.channel, leads):
            if reason is None:
                eligible.append((lead, recipient))
            else:
                setattr(skipped, reason, getattr(skipped, reason) + 1)
        return eligible, skipped

    def audience(self, user_id: int, channel: str) -> list[CategoryAudience]:
        """Per category, how many leads a campaign on this channel would reach.

        Lets the user launch a campaign by category without picking leads one
        by one, and shows how much of each category was already contacted.
        """
        leads = self.repository.leads.get_all_by_user(user_id)
        groups: dict[str, dict[str, int]] = {}
        for lead, _, reason in self._triage(user_id, channel, leads):
            if not lead.categoria:
                continue
            group = groups.setdefault(
                lead.categoria, {"total": 0, "elegiveis": 0, "ja_contatados": 0}
            )
            group["total"] += 1
            if reason is None:
                group["elegiveis"] += 1
            elif reason == "ja_contatado":
                group["ja_contatados"] += 1
        return sorted(
            (CategoryAudience(categoria=name, **counts) for name, counts in groups.items()),
            key=lambda c: (-c.elegiveis, c.categoria.lower()),
        )

    def preview(self, user_id: int, data: CampaignCreate) -> CampaignPreview:
        eligible, skipped = self._plan(user_id, data)
        samples = [
            MessageSample(
                nome=lead.nome,
                recipient=recipient,
                body=render_message(data.template, lead.nome, lead.categoria),
            )
            for lead, recipient in eligible[:PREVIEW_SAMPLES]
        ]
        return CampaignPreview(eligible=len(eligible), skipped=skipped, samples=samples)

    def create(self, user_id: int, data: CampaignCreate) -> CampaignCreated:
        eligible, skipped = self._plan(user_id, data)
        if not eligible:
            raise HTTPException(
                status_code=422,
                detail="Nenhum lead selecionado pode receber mensagem por este canal.",
            )

        now = utcnow()
        local = now + timedelta(hours=PACING[data.channel].utc_offset_hours)
        name = data.name or f"{CHANNEL_LABELS[data.channel]} {local:%d/%m %H:%M}"
        campaign = Campaign(
            id_user=user_id,
            name=name,
            channel=data.channel,
            template=data.template,
            status="running",
            created_at=now,
        )
        messages = [
            OutboundMessage(
                id_lead=lead.id_lead,
                channel=data.channel,
                recipient=recipient,
                body=render_message(data.template, lead.nome, lead.categoria),
                status="pending",
                attempts=0,
                created_at=now,
            )
            for lead, recipient in eligible
        ]
        campaign = self.repository.create_campaign(campaign, messages)
        return CampaignCreated(
            campaign=self._to_response(campaign),
            queued=len(messages),
            skipped=skipped,
        )

    # ─── Reading and controlling campaigns ───────────────────────────────────

    def _to_response(
        self, campaign: Campaign, counts: dict[str, int] | None = None
    ) -> CampaignResponse:
        if counts is None:
            counts = self.repository.status_counts([campaign.id_campaign])[
                campaign.id_campaign
            ]
        return CampaignResponse(
            id_campaign=campaign.id_campaign,
            name=campaign.name,
            channel=campaign.channel,
            template=campaign.template,
            status=campaign.status,
            created_at=_aware(campaign.created_at),
            total=sum(counts.values()),
            counts=StatusCounts(**counts),
        )

    def _get_owned(self, campaign_id: int, user_id: int) -> Campaign:
        campaign = self.repository.get_campaign(campaign_id, user_id)
        if campaign is None:
            raise HTTPException(status_code=404, detail="Campanha nao encontrada.")
        return campaign

    def list_campaigns(self, user_id: int) -> list[CampaignResponse]:
        campaigns = self.repository.list_campaigns(user_id)
        counts = self.repository.status_counts([c.id_campaign for c in campaigns])
        return [self._to_response(c, counts[c.id_campaign]) for c in campaigns]

    def get_campaign(self, campaign_id: int, user_id: int) -> CampaignResponse:
        return self._to_response(self._get_owned(campaign_id, user_id))

    def list_messages(
        self,
        campaign_id: int,
        user_id: int,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> MessagesPage:
        self._get_owned(campaign_id, user_id)
        rows, total = self.repository.list_messages(campaign_id, status, skip, limit)
        items = [
            MessageResponse(
                id_message=message.id_message,
                id_lead=message.id_lead,
                nome=nome,
                recipient=message.recipient,
                body=message.body,
                status=message.status,
                attempts=message.attempts,
                last_error=message.last_error,
                sent_at=_aware(message.sent_at),
            )
            for message, nome in rows
        ]
        return MessagesPage(items=items, total=total, skip=skip, limit=limit)

    def _transition(
        self, campaign_id: int, user_id: int, allowed_from: tuple[str, ...], to: str
    ) -> Campaign:
        campaign = self._get_owned(campaign_id, user_id)
        if campaign.status == to:
            return campaign
        if campaign.status not in allowed_from:
            raise HTTPException(
                status_code=409,
                detail=f"Campanha com status '{campaign.status}' nao pode ir para '{to}'.",
            )
        return self.repository.set_campaign_status(campaign, to)

    def pause(self, campaign_id: int, user_id: int) -> CampaignResponse:
        campaign = self._transition(campaign_id, user_id, ("running",), "paused")
        return self._to_response(campaign)

    def resume(self, campaign_id: int, user_id: int) -> CampaignResponse:
        campaign = self._transition(campaign_id, user_id, ("paused",), "running")
        # Everything may have failed or been sent while it was paused.
        self.repository.complete_if_done(campaign.id_campaign)
        return self.get_campaign(campaign_id, user_id)

    def cancel(self, campaign_id: int, user_id: int) -> CampaignResponse:
        campaign = self._transition(
            campaign_id, user_id, ("running", "paused"), "cancelled"
        )
        self.repository.cancel_waiting_messages(campaign.id_campaign, utcnow())
        return self._to_response(campaign)

    # ─── Sender accounts ─────────────────────────────────────────────────────

    def channel_status(self, channel: str) -> ChannelStatus:
        now = utcnow()
        pacing = PACING[channel]
        state = self.repository.get_channel(channel)
        sent_today = self.repository.sent_since(channel, local_day_start(now, pacing))
        paused = state.paused_until if state.paused_until and state.paused_until > now else None
        online = (
            state.last_seen_at is not None
            and (now - state.last_seen_at).total_seconds() <= WORKER_STALE_SECONDS
        )
        return ChannelStatus(
            channel=channel,
            health=state.health,
            health_detail=state.health_detail,
            qr_code=state.qr_code,
            worker_online=online,
            paused_until=_aware(paused),
            next_send_at=_aware(
                blocked_until(now, pacing, state.next_allowed_at, paused, sent_today)
            ),
            sent_today=sent_today,
            daily_cap=pacing.daily_cap,
            queued=self.repository.queued(channel),
            reconnect_pending=state.reconnect_requested_at is not None,
            needs_code=state.needs_code,
            code_pending=state.verification_code is not None,
        )

    def unpause_channel(self, channel: str) -> ChannelStatus:
        """Lift a block pause by hand, once the account is known to be fine."""
        state = self.repository.get_channel(channel)
        state.paused_until = None
        self.repository.save()
        return self.channel_status(channel)

    def request_reconnect(self, channel: str) -> ChannelStatus:
        """Ask the worker to restart the session, which yields a fresh QR code."""
        state = self.repository.get_channel(channel)
        state.reconnect_requested_at = utcnow()
        state.qr_code = None
        self.repository.save()
        return self.channel_status(channel)

    def submit_verification_code(self, channel: str, code: str) -> ChannelStatus:
        """Keep the login code the user typed until the worker picks it up."""
        state = self.repository.get_channel(channel)
        state.verification_code = code.replace(" ", "")
        self.repository.save()
        return self.channel_status(channel)

    def report_health(self, channel: str, report: HealthReport) -> HealthAck:
        now = utcnow()
        state = self.repository.get_channel(channel)
        state.last_seen_at = now
        state.health = report.state
        state.health_detail = report.detail
        state.qr_code = report.qr_code if report.state == "disconnected" else None
        if report.state == "blocked":
            minutes = report.pause_minutes or PACING[channel].block_pause_hours * 60
            state.paused_until = now + timedelta(minutes=minutes)

        state.needs_code = report.state == "disconnected" and report.needs_code

        # Handed over once: the worker acts on them as it reads the answer.
        reconnect = state.reconnect_requested_at is not None
        code = state.verification_code
        state.reconnect_requested_at = None
        state.verification_code = None
        self.repository.save()
        return HealthAck(reconnect=reconnect, verification_code=code)

    # ─── Sending (called by the workers) ─────────────────────────────────────

    def claim(self, channel: str) -> ClaimResponse:
        """Hand the worker its next message, if the pacing allows one now.

        The worker never decides when to send: it asks, and waits for as long
        as it is told. That keeps every limit here, in the database.
        """
        now = utcnow()
        pacing = PACING[channel]
        state = self.repository.get_channel(channel)
        state.last_seen_at = now
        self.repository.save()

        # One message at a time per account. A live lease means a send is in
        # flight, or that a worker died and its message is not free yet.
        lease = self.repository.live_lease_until(channel, now)
        if lease:
            return ClaimResponse(retry_after_seconds=_seconds_until(now, lease))

        sent_today = self.repository.sent_since(channel, local_day_start(now, pacing))
        wait = blocked_until(
            now, pacing, state.next_allowed_at, state.paused_until, sent_today
        )
        if wait:
            return ClaimResponse(retry_after_seconds=_seconds_until(now, wait))

        lease_until = now + timedelta(seconds=LEASE_SECONDS)
        while True:
            message = self.repository.claim_next(channel, now, lease_until)
            if message is None:
                return ClaimResponse(retry_after_seconds=IDLE_POLL_SECONDS)

            if message.attempts <= MAX_ATTEMPTS:
                return ClaimResponse(
                    message=ClaimedMessage(
                        id_message=message.id_message,
                        recipient=message.recipient,
                        body=message.body,
                        attempts=message.attempts,
                    )
                )

            # Claimed again and again without a report: whatever happens while
            # sending this one kills the worker. Stop feeding it.
            message.status = "failed"
            message.locked_until = None
            message.last_error = "Envio interrompido repetidamente."
            self.repository.save()
            self.repository.complete_if_done(message.id_campaign)

    def report(self, message_id: int, result: SendResult) -> None:
        message = self.repository.get_message(message_id)
        if message is None:
            raise HTTPException(status_code=404, detail="Mensagem nao encontrada.")
        if message.status != "sending":
            # A repeated or late report. The first one already counted.
            return

        now = utcnow()
        pacing = PACING[message.channel]
        state = self.repository.get_channel(message.channel)
        message.locked_until = None

        if result.outcome == "sent":
            message.status = "sent"
            message.sent_at = now
            message.last_error = None
            state.next_allowed_at, state.sent_in_chunk = after_send(
                now, pacing, state.sent_in_chunk
            )
        elif result.outcome == "failed":
            message.status = "failed"
            message.last_error = result.error
        elif result.outcome == "retry":
            message.last_error = result.error
            if message.attempts >= MAX_ATTEMPTS:
                message.status = "failed"
            else:
                message.status = "pending"
                backoff = RETRY_BASE_SECONDS * 2 ** (message.attempts - 1)
                message.next_attempt_at = now + timedelta(seconds=backoff)
        else:  # release
            # The account could not send at all. Not this message's fault, so
            # the attempt does not count.
            message.status = "pending"
            message.attempts = max(0, message.attempts - 1)
            message.next_attempt_at = None

        if result.outcome in ("failed", "retry"):
            # Nothing was delivered, but the worker still acted on the
            # platform: opened a profile, clicked, checked a number. That is
            # what anti-spam counts, so it is paced like a send. Without this,
            # a run of failures went out every few seconds.
            state.next_allowed_at, state.sent_in_chunk = after_send(
                now, pacing, state.sent_in_chunk
            )

        self.repository.save()
        self.repository.complete_if_done(message.id_campaign)
