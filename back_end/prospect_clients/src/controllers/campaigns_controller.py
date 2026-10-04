from http import HTTPStatus
from typing import List, Literal

from fastapi import APIRouter, Depends

from prospect_clients.src.configurations.dependencies import service_provider
from prospect_clients.src.configurations.messaging import CHANNELS
from prospect_clients.src.models.schemas.campaigns import (
    CampaignCreate,
    CampaignCreated,
    CampaignPreview,
    CampaignResponse,
    CategoryAudience,
    Channel,
    ChannelStatus,
    MessagesPage,
    VerificationCode,
)
from prospect_clients.src.repositories.campaigns_repository import CampaignsRepository
from prospect_clients.src.services.campaigns_service import CampaignsService
from prospect_clients.src.utils.security import get_current_user

router = APIRouter(tags=["Campaigns"])

_get_service = service_provider(CampaignsService, CampaignsRepository)

MessageStatus = Literal["pending", "sending", "sent", "failed", "cancelled"]


@router.post(
    "/campaigns/preview",
    response_model=CampaignPreview,
    summary="Preview who a campaign would reach and how the message reads",
)
def preview_campaign(
    data: CampaignCreate,
    service: CampaignsService = Depends(_get_service),
    current_user: dict = Depends(get_current_user),
):
    return service.preview(current_user["user_id"], data)


@router.post(
    "/campaigns",
    status_code=HTTPStatus.CREATED,
    response_model=CampaignCreated,
    summary="Queue a batch of messages",
    description=(
        "Stores one message per eligible lead and returns right away. The "
        "sender workers deliver them in chunks, at the channel's pace."
    ),
)
def create_campaign(
    data: CampaignCreate,
    service: CampaignsService = Depends(_get_service),
    current_user: dict = Depends(get_current_user),
):
    return service.create(current_user["user_id"], data)


@router.get(
    "/campaigns",
    response_model=List[CampaignResponse],
    summary="List campaigns for current user",
)
def list_campaigns(
    service: CampaignsService = Depends(_get_service),
    current_user: dict = Depends(get_current_user),
):
    return service.list_campaigns(current_user["user_id"])


# Declared before /campaigns/{campaign_id}, which would otherwise take
# "audience" as an id and reject it.
@router.get(
    "/campaigns/audience",
    response_model=List[CategoryAudience],
    summary="Per category, how many leads a campaign on a channel would reach",
)
def campaign_audience(
    channel: Channel,
    service: CampaignsService = Depends(_get_service),
    current_user: dict = Depends(get_current_user),
):
    return service.audience(current_user["user_id"], channel)


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: int,
    service: CampaignsService = Depends(_get_service),
    current_user: dict = Depends(get_current_user),
):
    return service.get_campaign(campaign_id, current_user["user_id"])


@router.get("/campaigns/{campaign_id}/messages", response_model=MessagesPage)
def list_campaign_messages(
    campaign_id: int,
    status: MessageStatus | None = None,
    skip: int = 0,
    limit: int = 50,
    service: CampaignsService = Depends(_get_service),
    current_user: dict = Depends(get_current_user),
):
    return service.list_messages(
        campaign_id, current_user["user_id"], status=status, skip=skip, limit=limit
    )


@router.post("/campaigns/{campaign_id}/pause", response_model=CampaignResponse)
def pause_campaign(
    campaign_id: int,
    service: CampaignsService = Depends(_get_service),
    current_user: dict = Depends(get_current_user),
):
    return service.pause(campaign_id, current_user["user_id"])


@router.post("/campaigns/{campaign_id}/resume", response_model=CampaignResponse)
def resume_campaign(
    campaign_id: int,
    service: CampaignsService = Depends(_get_service),
    current_user: dict = Depends(get_current_user),
):
    return service.resume(campaign_id, current_user["user_id"])


@router.post("/campaigns/{campaign_id}/cancel", response_model=CampaignResponse)
def cancel_campaign(
    campaign_id: int,
    service: CampaignsService = Depends(_get_service),
    current_user: dict = Depends(get_current_user),
):
    return service.cancel(campaign_id, current_user["user_id"])


@router.get(
    "/channels",
    response_model=List[ChannelStatus],
    summary="State of each sender account",
    description="Connection, pause, next send time and today's count per channel.",
)
def list_channels(
    service: CampaignsService = Depends(_get_service),
    _: dict = Depends(get_current_user),
):
    return [service.channel_status(channel) for channel in CHANNELS]


@router.post(
    "/channels/{channel}/reconnect",
    response_model=ChannelStatus,
    summary="Ask for a fresh session and QR code",
    description=(
        "The sender worker restarts the session on its next health report, "
        "within a few seconds, and the new QR code shows up in GET /channels."
    ),
)
def reconnect_channel(
    channel: Channel,
    service: CampaignsService = Depends(_get_service),
    _: dict = Depends(get_current_user),
):
    return service.request_reconnect(channel)


@router.post(
    "/channels/{channel}/verification-code",
    response_model=ChannelStatus,
    summary="Hand the login verification code to the sender worker",
    description=(
        "Instagram may ask for a code sent by e-mail or SMS when the sender "
        "account logs in. The worker types it on its next health report."
    ),
)
def submit_verification_code(
    channel: Channel,
    data: VerificationCode,
    service: CampaignsService = Depends(_get_service),
    _: dict = Depends(get_current_user),
):
    return service.submit_verification_code(channel, data.code)


@router.post(
    "/channels/{channel}/unpause",
    response_model=ChannelStatus,
    summary="Lift a block pause by hand",
)
def unpause_channel(
    channel: Channel,
    service: CampaignsService = Depends(_get_service),
    _: dict = Depends(get_current_user),
):
    return service.unpause_channel(channel)
