from typing import List
from http import HTTPStatus
from fastapi import APIRouter, Depends, Query

from prospect_clients.src.configurations.dependencies import service_provider
from prospect_clients.src.utils.security import get_current_user
from prospect_clients.src.models.schemas.leads import LeadSchema, LeadsPage
from prospect_clients.src.repositories.leads_repository import LeadsRepository
from prospect_clients.src.services.leads_service import LeadsService

router = APIRouter(prefix="/leads", tags=["Leads"])

_get_service = service_provider(LeadsService, LeadsRepository)


@router.get(
    "/",
    response_model=LeadsPage,
    summary="List leads for current user",
)
def list_leads(
    skip: int = 0,
    limit: int = 100,
    nome: str | None = None,
    categoria: List[str] | None = Query(None),
    telefone: str | None = None,
    endereco: str | None = None,
    site: str | None = None,
    service: LeadsService = Depends(_get_service),
    current_user: dict = Depends(get_current_user),
):
    return service.get_leads(
        current_user["user_id"],
        skip=skip,
        limit=limit,
        nome=nome,
        categoria=categoria,
        telefone=telefone,
        endereco=endereco,
        site=site,
    )


@router.get(
    "/categories",
    response_model=List[str],
    summary="List distinct lead categories for current user",
)
def list_categories(
    service: LeadsService = Depends(_get_service),
    current_user: dict = Depends(get_current_user),
):
    return service.get_categories(current_user["user_id"])


@router.post(
    "/",
    status_code=HTTPStatus.CREATED,
    summary="Register multiple leads",
    description="Register multiple leads in the database, ignoring duplicates based"
    " on the 'nome' field. and create user lead history entries.",
)
def create_leads(
    leads: List[LeadSchema],
    service: LeadsService = Depends(_get_service),
    current_user: dict = Depends(get_current_user),
):
    return service.register_leads(leads, current_user["user_id"])
