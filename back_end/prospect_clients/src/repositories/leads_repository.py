from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from prospect_clients.src.models.tables.leads import Leads, UserLeadHistory

# Quantas categorias o painel mostra antes de agrupar o resto em "outras".
TOP_CATEGORIES = 10


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
        self, user_id: int, lead_ids: list[int], operation_id: int | None = None
    ) -> list[UserLeadHistory]:
        entries = [
            UserLeadHistory(
                user_id=user_id, lead_id=lead_id, id_operation=operation_id
            )
            for lead_id in lead_ids
        ]
        self.db.add_all(entries)
        self.db.commit()
        return entries

    def get_by_operation(self, operation_id: int, user_id: int) -> list[Leads]:
        """Leads found by one operation, restricted to the user who owns it."""
        return (
            self.db.query(Leads)
            .join(UserLeadHistory, UserLeadHistory.lead_id == Leads.id_lead)
            .filter(UserLeadHistory.id_operation == operation_id)
            .filter(UserLeadHistory.user_id == user_id)
            .distinct()
            .order_by(Leads.nome)
            .all()
        )

    def _filtered_query(
        self,
        user_id: int,
        nome: str | None = None,
        categoria: list[str] | None = None,
        telefone: str | None = None,
        endereco: str | None = None,
        site: str | None = None,
        origem: list[str] | None = None,
    ):
        query = (
            self.db.query(Leads)
            .join(UserLeadHistory, UserLeadHistory.lead_id == Leads.id_lead)
            .filter(UserLeadHistory.user_id == user_id)
        )

        # Filtros textuais parciais (case-insensitive)
        text_filters = {
            Leads.nome: nome,
            Leads.telefone: telefone,
            Leads.endereco: endereco,
            Leads.site: site,
        }
        for column, value in text_filters.items():
            if value:
                query = query.filter(column.ilike(f"%{value}%"))

        # Categoria: correspondencia exata por qualquer uma das selecionadas
        if categoria:
            query = query.filter(Leads.categoria.in_(categoria))

        # Origem: mesma ideia, "maps" e/ou "instagram"
        if origem:
            query = query.filter(Leads.origem.in_(origem))

        return query.distinct()

    def get_by_user(
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
    ) -> tuple[list[Leads], int]:
        query = self._filtered_query(
            user_id,
            nome=nome,
            categoria=categoria,
            telefone=telefone,
            endereco=endereco,
            site=site,
            origem=origem,
        )
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def get_stats(self, user_id: int) -> dict:
        """Aggregates for the dashboard, counted in the database.

        The page endpoint cannot answer these: it returns one page, so counting
        there would describe the page and not the base. Everything here is a
        COUNT over the user's whole set.
        """
        # Um lead pode aparecer várias vezes no histórico, uma por operação que
        # o encontrou, então o conjunto do usuário é o de ids distintos.
        meus_leads = (
            select(UserLeadHistory.lead_id)
            .where(UserLeadHistory.user_id == user_id)
            .distinct()
        )

        def contar(*condicoes) -> int:
            query = self.db.query(func.count(Leads.id_lead)).filter(
                Leads.id_lead.in_(meus_leads)
            )
            for condicao in condicoes:
                query = query.filter(condicao)
            return query.scalar() or 0

        def vazio(coluna):
            return or_(coluna.is_(None), coluna == "")

        def agrupar_por(coluna, limite=None):
            query = (
                self.db.query(coluna, func.count(Leads.id_lead))
                .filter(Leads.id_lead.in_(meus_leads))
                .group_by(coluna)
                .order_by(func.count(Leads.id_lead).desc())
            )
            if limite:
                query = query.limit(limite)
            return query.all()

        total = contar()
        categorias = agrupar_por(Leads.categoria, TOP_CATEGORIES)
        total_categorias = (
            self.db.query(func.count(func.distinct(Leads.categoria)))
            .filter(Leads.id_lead.in_(meus_leads))
            .filter(Leads.categoria.isnot(None))
            .scalar()
            or 0
        )

        return {
            "total": total,
            "por_origem": [
                {"origem": origem or "maps", "total": quantidade}
                for origem, quantidade in agrupar_por(Leads.origem)
            ],
            "por_categoria": [
                {"categoria": categoria or "Sem categoria", "total": quantidade}
                for categoria, quantidade in categorias
            ],
            "total_categorias": total_categorias,
            "sem_site": contar(vazio(Leads.site)),
            "sem_telefone": contar(vazio(Leads.telefone)),
            "sem_endereco": contar(vazio(Leads.endereco)),
            # Sem telefone nem site não há como abordar: é o número que diz
            # quanto da base é inútil para prospecção.
            "sem_contato": contar(vazio(Leads.telefone), vazio(Leads.site)),
        }

    def get_distinct_categories(self, user_id: int) -> list[str]:
        rows = (
            self.db.query(Leads.categoria)
            .join(UserLeadHistory, UserLeadHistory.lead_id == Leads.id_lead)
            .filter(UserLeadHistory.user_id == user_id)
            .filter(Leads.categoria.isnot(None))
            .distinct()
            .order_by(Leads.categoria)
            .all()
        )
        return [row[0] for row in rows]
