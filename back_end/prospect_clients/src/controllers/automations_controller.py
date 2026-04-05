from http import HTTPStatus
from fastapi import APIRouter, Depends

from prospect_clients.src.models.schemas.data_returned_selenium import LeadsResponse
from prospect_clients.src.utils.security import get_current_user
from prospect_clients.src.services.automations_service import AutomationsService

router = APIRouter()


def _get_service() -> AutomationsService:
    return AutomationsService()


@router.post(
    "/operations/maps/activate",
    status_code=HTTPStatus.OK,
    summary="Initiate lead scraping and messaging via Google Maps service",
    description=(
        "This endpoint triggers a service that searches for leads on Google Maps. "
        "Subsequently, it retrieves the contact number found and sends a message to it, "
        "using the content provided in the 'message_user' parameter."
    ),
    response_description="A confirmation message that the scraping and messaging process has started.",
)
def send_message_maps_service(
    serach_text: str,
    message_user: str,
    title: str = None,
    current_user: dict = Depends(get_current_user),
    service: AutomationsService = Depends(_get_service),
):
    return service.activate_maps_scraping(
        search_text=serach_text,
        message_user=message_user,
        user_id=current_user["user_id"],
        token=current_user["token"],
        title=title,
    )


@router.put(
    "/operations/maps/deactivate",
    status_code=HTTPStatus.OK,
    summary="Send message of service for stopping leads scraping",
    response_description="A confirmation message that the scraping process has stopped.",
)
def send_message_stop_maps_service(
    id_operation: int,
    current_user: dict = Depends(get_current_user),
    service: AutomationsService = Depends(_get_service),
):
    return service.deactivate_maps_scraping(
        id_operation=id_operation,
        user_id=current_user["user_id"],
        token=current_user["token"],
    )


@router.get(
    "/leads",
    response_model=LeadsResponse,
    status_code=HTTPStatus.OK,
    response_description="A list of leads with their contact information.",
)
def read_route(
    text_serach: str,
    _: dict = Depends(get_current_user),
    service: AutomationsService = Depends(_get_service),
):
    return service.scrape_leads_from_maps(text_serach)
