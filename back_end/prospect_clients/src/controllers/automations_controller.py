from http import HTTPStatus
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from prospect_clients.src.configurations.database import get_db
from prospect_clients.src.models.schemas.data_returned_selenium import LeadsResponse
from prospect_clients.src.models.schemas.operations import OperationCreate, OperationResponse
from prospect_clients.src.utils.security import get_current_user
from prospect_clients.src.services.automations_service import AutomationsService
from prospect_clients.src.services.operations_service import OperationsService
from prospect_clients.src.repositories.operations_repository import OperationsRepository

router = APIRouter()


@router.post(
    "/operations/maps/activate",
    status_code=HTTPStatus.CREATED,
    response_model=OperationResponse,
    summary="Initiate lead scraping via Google Maps",
    description=(
        "Creates an operation in the database and triggers the scraping service via MQTT. "
        "Returns the created operation immediately so the UI can track it."
    ),
)
def send_message_maps_service(
    serach_text: str,
    message_user: str,
    title: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Cria a operação no banco imediatamente
    ops_service = OperationsService(OperationsRepository(db))
    operation = ops_service.create_operation(
        OperationCreate(
            operation_name=title or serach_text,
            search_text=serach_text,
            message_for_lead=message_user,
        ),
        user_id=current_user["user_id"],
    )

    # Publica no MQTT com o ID já criado (maps_service usa, não recria)
    AutomationsService().activate_maps_scraping(
        search_text=serach_text,
        message_user=message_user,
        user_id=current_user["user_id"],
        token=current_user["token"],
        id_operation=operation.id_operation,
        title=title,
    )

    return operation


@router.put(
    "/operations/maps/deactivate",
    status_code=HTTPStatus.OK,
    summary="Stop leads scraping",
    response_description="A confirmation message that the scraping process has stopped.",
)
def send_message_stop_maps_service(
    id_operation: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Mark as stopped in the database right away so the UI reflects it,
    # without depending on the async thread teardown in maps_service.
    # Best-effort: if the operation does not exist, proceed without error (idempotent).
    OperationsRepository(db).update_status(id_operation, 0)

    # MQTT continua sendo enviado para o maps_service encerrar o scraper de fato.
    AutomationsService().deactivate_maps_scraping(
        id_operation=id_operation,
        user_id=current_user["user_id"],
        token=current_user["token"],
    )
    return {"message": "Scraping process stopped"}


@router.get(
    "/leads",
    response_model=LeadsResponse,
    status_code=HTTPStatus.OK,
    response_description="A list of leads with their contact information.",
)
def read_route(
    text_serach: str,
    _: dict = Depends(get_current_user),
):
    return AutomationsService().scrape_leads_from_maps(text_serach)
