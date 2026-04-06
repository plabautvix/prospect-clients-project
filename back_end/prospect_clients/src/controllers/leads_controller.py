from typing import List
from http import HTTPStatus
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from prospect_clients.src.configurations.database import get_db
from prospect_clients.src.utils.security import get_current_user
from prospect_clients.src.models.schemas.leads import LeadSchema
from prospect_clients.src.repositories.leads_repository import LeadsRepository
from prospect_clients.src.services.leads_service import LeadsService

router = APIRouter(prefix="/leads", tags=["Leads"])


def _get_service(db: Session = Depends(get_db)) -> LeadsService:
    return LeadsService(LeadsRepository(db))


@router.get(
    "/",
    summary="List leads for current user",
)
def list_leads(
    skip: int = 0,
    limit: int = 100,
    service: LeadsService = Depends(_get_service),
    current_user: dict = Depends(get_current_user),
):
    return service.get_leads(current_user["user_id"], skip=skip, limit=limit)


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
