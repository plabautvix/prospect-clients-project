from prospect_clients.src.models.schemas.leads import LeadSchema
from prospect_clients.src.repositories.leads_repository import LeadsRepository
from prospect_clients.src.repositories.user_repository import UserRepository
from prospect_clients.src.services.leads_service import LeadsService


class TestLeadsRepository:
    def test_bulk_upsert_and_history(self, db):
        user_repo = UserRepository(db)
        user = user_repo.create(email="lead@test.com", hashed_password="hash")

        repo = LeadsRepository(db)
        leads_data = [
            {"nome": "Empresa A", "telefone": "123", "endereco": None, "site": None, "foto": None, "categoria": None},
            {"nome": "Empresa B", "telefone": "456", "endereco": None, "site": None, "foto": None, "categoria": None},
        ]

        result = repo.bulk_upsert_leads(leads_data)
        assert len(result) == 2

        # Duplicate insert should not fail
        result2 = repo.bulk_upsert_leads(leads_data)
        assert len(result2) == 2

    def test_create_lead_history(self, db):
        user_repo = UserRepository(db)
        user = user_repo.create(email="hist@test.com", hashed_password="hash")

        repo = LeadsRepository(db)
        leads = repo.bulk_upsert_leads([
            {"nome": "Hist Lead", "telefone": None, "endereco": None, "site": None, "foto": None, "categoria": None},
        ])

        entries = repo.create_lead_history_entries(user.id_person, [leads[0].id_lead])
        assert len(entries) == 1
        assert entries[0].user_id == user.id_person


class TestLeadsService:
    def test_register_leads(self, db):
        user_repo = UserRepository(db)
        user = user_repo.create(email="svc@test.com", hashed_password="hash")

        service = LeadsService(LeadsRepository(db))
        leads = [
            LeadSchema(nome="Svc Lead 1", telefone="111"),
            LeadSchema(nome="Svc Lead 2", telefone="222"),
        ]

        result = service.register_leads(leads, user.id_person)
        assert len(result) == 2

    def test_register_empty_leads(self, db):
        service = LeadsService(LeadsRepository(db))
        result = service.register_leads([], user_id=1)
        assert result == []


class TestLeadsEndpoints:
    def _get_token(self, client):
        client.post("/users/", json={"email": "leads@test.com", "password": "pass"})
        login = client.post(
            "/users/login",
            data={"username": "leads@test.com", "password": "pass"},
        )
        return login.json()["access_token"]

    def test_create_leads_endpoint(self, client):
        token = self._get_token(client)
        response = client.post(
            "/leads/",
            json=[
                {"nome": "Endpoint Lead", "telefone": "999"},
                {"nome": "Endpoint Lead 2", "telefone": "888"},
            ],
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 2

    def test_create_leads_unauthenticated(self, client):
        response = client.post("/leads/", json=[{"nome": "No Auth"}])
        assert response.status_code in (401, 403)
