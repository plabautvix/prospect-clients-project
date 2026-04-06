from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from prospect_clients.src.models.tables.leads import Leads, UserLeadHistory


class LeadsRepository:
    def __init__(self, db: Session):
        self.db = db

    def bulk_upsert_leads(self, leads_data: list[dict]) -> list[Leads]:
        stmt = sqlite_insert(Leads).values(leads_data)
        stmt = stmt.on_conflict_do_nothing(index_elements=["nome"])
        self.db.execute(stmt)
        self.db.commit()

        names = [data["nome"] for data in leads_data]
        return self.db.query(Leads).filter(Leads.nome.in_(names)).all()

    def create_lead_history_entries(
        self, user_id: int, lead_ids: list[int]
    ) -> list[UserLeadHistory]:
        entries = [
            UserLeadHistory(user_id=user_id, lead_id=lead_id)
            for lead_id in lead_ids
        ]
        self.db.add_all(entries)
        self.db.commit()
        return entries

    def get_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> list[Leads]:
        return (
            self.db.query(Leads)
            .join(UserLeadHistory, UserLeadHistory.lead_id == Leads.id_lead)
            .filter(UserLeadHistory.user_id == user_id)
            .distinct()
            .offset(skip)
            .limit(limit)
            .all()
        )
