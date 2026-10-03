from fastapi import APIRouter, Depends

from prospect_clients.src.configurations.dependencies import service_provider
from prospect_clients.src.models.schemas.campaigns import (
    Channel,
    ClaimResponse,
    HealthAck,
    HealthReport,
    SendResult,
)
from prospect_clients.src.repositories.campaigns_repository import CampaignsRepository
from prospect_clients.src.services.campaigns_service import CampaignsService
from prospect_clients.src.utils.security import require_service

# Everything a sender worker calls, and nothing a user can. Workers are pulled,
# never pushed: they ask for the next message, so a worker that is down simply
# stops asking and its messages wait in the database.
router = APIRouter(prefix="/outbox", tags=["Outbox (service only)"])

_get_service = service_provider(CampaignsService, CampaignsRepository)


@router.post(
    "/{channel}/claim",
    response_model=ClaimResponse,
    summary="Take the next message to send, if the pacing allows",
    description=(
        "Returns one leased message, or retry_after_seconds when nothing may "
        "be sent now. A message not reported before its lease ends is handed "
        "out again."
    ),
)
def claim_message(
    channel: Channel,
    service: CampaignsService = Depends(_get_service),
    _: bool = Depends(require_service),
):
    return service.claim(channel)


@router.post(
    "/messages/{message_id}/result",
    summary="Report how a claimed message went",
)
def report_result(
    message_id: int,
    result: SendResult,
    service: CampaignsService = Depends(_get_service),
    _: bool = Depends(require_service),
):
    service.report(message_id, result)
    return {"ok": True}


@router.post(
    "/{channel}/health",
    response_model=HealthAck,
    summary="Report the state of the sender account",
    description=(
        "Connected, waiting for a QR scan, or blocked by the platform. The "
        "answer says whether the user asked for a fresh session."
    ),
)
def report_health(
    channel: Channel,
    report: HealthReport,
    service: CampaignsService = Depends(_get_service),
    _: bool = Depends(require_service),
):
    return service.report_health(channel, report)
