from typing import List
from http import HTTPStatus
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from prospect_clients.src.models.tables.leads import Leads, UserLeadHistory
from prospect_clients.src.models.schemas.leads import LeadSchema
from prospect_clients.src.configurations.database import get_db
from prospect_clients.src.utils.security import get_current_user
router = APIRouter(prefix="/leads", tags=["Leads"])

@router.post(
    "/",
    status_code=HTTPStatus.CREATED,
    summary="Register multiple leads",
    description="Register multiple leads in the database, ignoring duplicates based" \
    " on the 'nome' field. and create user lead history entries.",
)
def create_leads(
    leads: List[LeadSchema],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    leads_data = [lead.model_dump(exclude={"id_lead"}) for lead in leads]

    if not leads_data:
        return []

    stmt = sqlite_insert(Leads).values(leads_data)
    stmt = stmt.on_conflict_do_nothing(index_elements=['nome'])
    db.execute(stmt)
    db.commit()

    names = [data["nome"] for data in leads_data]
    leads_with_ids = db.query(Leads).filter(Leads.nome.in_(names)).all()

    lead_map = {lead.nome: lead.id_lead for lead in leads_with_ids}

    leads_history_entries = [
        UserLeadHistory(user_id=current_user["user_id"], lead_id=lead_map.get(lead.nome))
        for lead in leads
    ]

    db.add_all(leads_history_entries)
    db.commit()

    return leads_with_ids
