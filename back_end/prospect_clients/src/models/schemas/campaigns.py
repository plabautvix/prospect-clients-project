from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

Channel = Literal["whatsapp", "instagram"]


class CampaignLeadFilters(BaseModel):
    """Same filters as GET /leads/, to target every lead a search shows."""

    nome: Optional[str] = None
    categoria: Optional[List[str]] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    site: Optional[str] = None
    origem: Optional[List[str]] = None
    contato: Optional[Literal["nao_contatado", "na_fila", "enviado"]] = None


class CampaignCreate(BaseModel):
    channel: Channel
    template: str = Field(..., min_length=1, max_length=1000)
    name: Optional[str] = Field(None, max_length=255)
    lead_ids: Optional[List[int]] = Field(
        None, description="Leads picked by hand. Use this or filters."
    )
    filters: Optional[CampaignLeadFilters] = Field(
        None, description="Every lead matching these filters. Use this or lead_ids."
    )

    @model_validator(mode="after")
    def one_target(self):
        if bool(self.lead_ids) == (self.filters is not None):
            raise ValueError("Informe lead_ids ou filters, apenas um dos dois.")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "channel": "whatsapp",
                "template": "{Olá|Oi} {nome}, tudo bem?",
                "lead_ids": [1, 2, 3],
            }
        }
    }


class SkippedCounts(BaseModel):
    sem_contato: int = Field(0, description="No usable phone or handle for the channel.")
    nao_contatar: int = Field(0, description="Lead marked as do not contact.")
    ja_contatado: int = Field(0, description="Already messaged on this channel.")
    duplicado: int = Field(0, description="Same recipient twice in the selection.")


class CategoryAudience(BaseModel):
    """How a category would fare in a campaign on one channel."""

    categoria: str
    total: int = Field(..., description="Leads of the user in the category.")
    elegiveis: int = Field(..., description="Would get a message on this channel now.")
    ja_contatados: int = Field(..., description="Already messaged on this channel.")


class MessageSample(BaseModel):
    nome: str
    recipient: str
    body: str


class CampaignPreview(BaseModel):
    eligible: int
    skipped: SkippedCounts
    samples: List[MessageSample]


class StatusCounts(BaseModel):
    pending: int = 0
    sending: int = 0
    sent: int = 0
    failed: int = 0
    cancelled: int = 0


class CampaignResponse(BaseModel):
    id_campaign: int
    name: str
    channel: str
    template: str
    status: str
    created_at: datetime
    total: int
    counts: StatusCounts


class CampaignCreated(BaseModel):
    campaign: CampaignResponse
    queued: int
    skipped: SkippedCounts


class MessageResponse(BaseModel):
    id_message: int
    id_lead: int
    nome: str
    recipient: str
    body: str
    status: str
    attempts: int
    last_error: Optional[str] = None
    sent_at: Optional[datetime] = None


class MessagesPage(BaseModel):
    items: List[MessageResponse]
    total: int
    skip: int
    limit: int


class ChannelStatus(BaseModel):
    channel: str
    health: str
    health_detail: Optional[str] = None
    qr_code: Optional[str] = None
    worker_online: bool
    paused_until: Optional[datetime] = None
    next_send_at: Optional[datetime] = Field(
        None, description="When the next send may go out. Null means right away."
    )
    sent_today: int
    daily_cap: int
    queued: int = Field(..., description="Messages waiting in running campaigns.")
    reconnect_pending: bool = Field(
        False, description="A new QR code was asked for and the worker has not taken it yet."
    )
    needs_code: bool = Field(
        False, description="The platform asked for a login verification code."
    )
    code_pending: bool = Field(
        False, description="A code was typed and the worker has not taken it yet."
    )


# ─── Service side (X-Service-Key) ─────────────────────────────────────────────


class ClaimedMessage(BaseModel):
    id_message: int
    recipient: str
    body: str
    attempts: int


class ClaimResponse(BaseModel):
    message: Optional[ClaimedMessage] = None
    retry_after_seconds: Optional[int] = Field(
        None, description="Set when there is nothing to send now: ask again after it."
    )


class SendResult(BaseModel):
    outcome: Literal["sent", "failed", "retry", "release"] = Field(
        ...,
        description=(
            "sent: delivered. failed: will never work (no WhatsApp, no profile). "
            "retry: transient error, try again later. release: the account is "
            "not usable right now; the message goes back untouched."
        ),
    )
    error: Optional[str] = Field(None, max_length=500)


class HealthReport(BaseModel):
    state: Literal["ok", "disconnected", "blocked"]
    detail: Optional[str] = Field(None, max_length=500)
    qr_code: Optional[str] = Field(None, description="Pairing QR code as a data URL.")
    pause_minutes: Optional[int] = Field(
        None, description="For blocked: how long to stop. Defaults to the channel setting."
    )
    needs_code: bool = Field(
        False, description="Waiting on a login verification code (Instagram)."
    )


class HealthAck(BaseModel):
    reconnect: bool = Field(
        False, description="The user asked for a fresh session: restart it now."
    )
    verification_code: Optional[str] = Field(
        None, description="Login verification code typed by the user, handed over once."
    )


class VerificationCode(BaseModel):
    code: str = Field(..., min_length=4, max_length=20, pattern=r"^[0-9A-Za-z ]+$")


class DoNotContactUpdate(BaseModel):
    lead_ids: List[int] = Field(..., min_length=1)
    nao_contatar: bool = True
