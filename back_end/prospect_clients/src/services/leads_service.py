from collections import Counter
from datetime import timezone

from opentelemetry import metrics

from prospect_clients.src.models.schemas.leads import (
    LeadContact,
    LeadResponse,
    LeadSchema,
)
from prospect_clients.src.repositories.leads_repository import LeadsRepository

leads_registered = metrics.get_meter(__name__).create_counter(
    "prospect.leads.registered",
    unit="{lead}",
    description="Leads received from the search services, by source",
)


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
        contato: str | None = None,
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
            contato=contato,
        )
        contacts = self.repository.contact_status(
            user_id, [lead.id_lead for lead in items]
        )
        rows = []
        for lead in items:
            row = LeadResponse.model_validate(lead)
            row.contatos = [
                LeadContact(
                    channel=c["channel"],
                    status=c["status"],
                    # Naive UTC from the database, tagged so the browser reads it as UTC.
                    sent_at=c["sent_at"].replace(tzinfo=timezone.utc) if c["sent_at"] else None,
                )
                for c in contacts.get(lead.id_lead, [])
            ]
            rows.append(row)
        return {"items": rows, "total": total, "skip": skip, "limit": limit}

    def get_stats(self, user_id: int) -> dict:
        return self.repository.get_stats(user_id)

    def get_categories(self, user_id: int) -> list[str]:
        return self.repository.get_distinct_categories(user_id)

    def set_do_not_contact(self, user_id: int, lead_ids: list[int], value: bool) -> int:
        return self.repository.set_do_not_contact(user_id, lead_ids, value)

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

        for origem, count in Counter(lead.origem for lead in leads).items():
            leads_registered.add(count, {"source": origem})

        return persisted_leads
