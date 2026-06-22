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

    def _seed_user_with_leads(self, db, email, leads_data):
        user_repo = UserRepository(db)
        user = user_repo.create(email=email, hashed_password="hash")
        repo = LeadsRepository(db)
        leads = repo.bulk_upsert_leads(leads_data)
        repo.create_lead_history_entries(user.id_person, [l.id_lead for l in leads])
        return user, repo

    def test_get_by_user_pagination(self, db):
        leads_data = [
            {"nome": f"Lead {i:02d}", "telefone": None, "endereco": None,
             "site": None, "foto": None, "categoria": None}
            for i in range(10)
        ]
        user, repo = self._seed_user_with_leads(db, "page@test.com", leads_data)

        items, total = repo.get_by_user(user.id_person, skip=0, limit=3)
        assert total == 10
        assert len(items) == 3

        items_page2, total2 = repo.get_by_user(user.id_person, skip=3, limit=3)
        assert total2 == 10
        assert len(items_page2) == 3
        # Páginas não se sobrepõem
        assert {l.id_lead for l in items}.isdisjoint({l.id_lead for l in items_page2})

    def test_get_by_user_filters(self, db):
        leads_data = [
            {"nome": "Padaria Sol", "telefone": "111", "endereco": "Rua A",
             "site": None, "foto": None, "categoria": "padaria"},
            {"nome": "Barbearia Lua", "telefone": "222", "endereco": "Rua B",
             "site": None, "foto": None, "categoria": "barbearia"},
            {"nome": "Padaria Estrela", "telefone": "333", "endereco": "Rua C",
             "site": None, "foto": None, "categoria": "padaria"},
        ]
        user, repo = self._seed_user_with_leads(db, "filter@test.com", leads_data)

        # Filtro por nome (parcial, case-insensitive)
        items, total = repo.get_by_user(user.id_person, nome="padaria")
        assert total == 2
        assert all("Padaria" in l.nome for l in items)

        # Filtro por categoria (lista, correspondência exata / IN)
        items, total = repo.get_by_user(user.id_person, categoria=["barbearia"])
        assert total == 1
        assert items[0].nome == "Barbearia Lua"

        # Múltiplas categorias selecionadas (OR via IN)
        items, total = repo.get_by_user(user.id_person, categoria=["padaria", "barbearia"])
        assert total == 3


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

    def test_list_leads_paginated_shape(self, client):
        token = self._get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        client.post(
            "/leads/",
            json=[
                {"nome": "Page Lead 1", "telefone": "1", "categoria": "padaria"},
                {"nome": "Page Lead 2", "telefone": "2", "categoria": "barbearia"},
            ],
            headers=headers,
        )

        response = client.get("/leads/", params={"skip": 0, "limit": 1}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["skip"] == 0
        assert data["limit"] == 1
        assert len(data["items"]) == 1
        assert "id_lead" in data["items"][0]

    def test_list_leads_filter(self, client):
        token = self._get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        client.post(
            "/leads/",
            json=[
                {"nome": "Filtro Padaria", "categoria": "padaria"},
                {"nome": "Filtro Barbearia", "categoria": "barbearia"},
            ],
            headers=headers,
        )

        response = client.get("/leads/", params={"categoria": "padaria"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["nome"] == "Filtro Padaria"

    def test_list_categories(self, client):
        token = self._get_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        client.post(
            "/leads/",
            json=[
                {"nome": "Cat Lead 1", "categoria": "padaria"},
                {"nome": "Cat Lead 2", "categoria": "barbearia"},
                {"nome": "Cat Lead 3", "categoria": "padaria"},
                {"nome": "Cat Lead 4", "categoria": None},
            ],
            headers=headers,
        )

        response = client.get("/leads/categories", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Distintas, sem None, ordenadas
        assert data == ["barbearia", "padaria"]
