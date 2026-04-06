from prospect_clients.src.models.schemas.leads import LeadSchema
from prospect_clients.src.repositories.leads_repository import LeadsRepository


class LeadsService:
    def __init__(self, repository: LeadsRepository):
        self.repository = repository

    def get_leads(self, user_id: int, skip: int = 0, limit: int = 100):
        return self.repository.get_by_user(user_id, skip=skip, limit=limit)

    def register_leads(self, leads: list[LeadSchema], user_id: int):
        leads_data = [lead.model_dump(exclude={"id_lead"}) for lead in leads]

        if not leads_data:
            return []

        persisted_leads = self.repository.bulk_upsert_leads(leads_data)

        lead_name_to_id = {lead.nome: lead.id_lead for lead in persisted_leads}
        lead_ids = [
            lead_name_to_id[lead.nome]
            for lead in leads
            if lead.nome in lead_name_to_id
        ]

        self.repository.create_lead_history_entries(user_id, lead_ids)

        return persisted_leads
