from prospect_clients.src.models.schemas.leads import LeadSchema
from prospect_clients.src.repositories.leads_repository import LeadsRepository


class LeadsService:
    def __init__(self, repository: LeadsRepository):
        self.repository = repository

    def get_leads(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        nome: str | None = None,
        categoria: list[str] | None = None,
        telefone: str | None = None,
        endereco: str | None = None,
        site: str | None = None,
        origem: list[str] | None = None,
    ):
        items, total = self.repository.get_by_user(
            user_id,
            skip=skip,
            limit=limit,
            nome=nome,
            categoria=categoria,
            telefone=telefone,
            endereco=endereco,
            site=site,
            origem=origem,
        )
        return {"items": items, "total": total, "skip": skip, "limit": limit}

    def get_stats(self, user_id: int) -> dict:
        return self.repository.get_stats(user_id)

    def get_categories(self, user_id: int) -> list[str]:
        return self.repository.get_distinct_categories(user_id)

    def get_leads_by_operation(self, operation_id: int, user_id: int):
        return self.repository.get_by_operation(operation_id, user_id)

    def register_leads(
        self,
        leads: list[LeadSchema],
        user_id: int,
        operation_id: int | None = None,
    ):
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

        self.repository.create_lead_history_entries(user_id, lead_ids, operation_id)

        return persisted_leads
