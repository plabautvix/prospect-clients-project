from http import HTTPStatus
from fastapi import APIRouter, Depends

from prospect_clients.src.configurations.dependencies import service_provider
from prospect_clients.src.utils.security import get_current_user, require_service
from prospect_clients.src.models.schemas.operations import (
    OperationCreate,
    OperationResponse,
    OperationStatusUpdate,
)
from prospect_clients.src.repositories.operations_repository import OperationsRepository
from prospect_clients.src.services.operations_service import OperationsService

router = APIRouter(prefix="/operations", tags=["Operations"])

_get_service = service_provider(OperationsService, OperationsRepository)


@router.get(
    "/",
    response_model=list[OperationResponse],
    summary="List operations for current user",
)
def list_operations(
    current_user: dict = Depends(get_current_user),
    service: OperationsService = Depends(_get_service),
):
    return service.get_operations(current_user["user_id"])


@router.post(
    "/",
    status_code=HTTPStatus.CREATED,
    response_model=OperationResponse,
    summary="Create a new operation",
)
def create_operation(
    data: OperationCreate,
    current_user: dict = Depends(get_current_user),
    service: OperationsService = Depends(_get_service),
):
    return service.create_operation(data, current_user["user_id"])


@router.patch(
    "/{operation_id}/status",
    response_model=OperationResponse,
    summary="Update operation status (service only)",
)
def update_operation_status(
    operation_id: int,
    data: OperationStatusUpdate,
    service: OperationsService = Depends(_get_service),
    _: bool = Depends(require_service),
):
    return service.update_status(operation_id, data.status)


@router.get(
    "/{operation_id}",
    response_model=OperationResponse,
    summary="Get operation by ID",
)
def get_operation(
    operation_id: int,
    current_user: dict = Depends(get_current_user),
    service: OperationsService = Depends(_get_service),
):
    return service.get_operation(operation_id)
