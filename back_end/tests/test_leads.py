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
    def _seed(self, client, db, email, leads):
        """Create a user, log in, seed leads via the service endpoint; return token."""
        from prospect_clients.src.configurations.auth import SERVICE_API_KEY
        from prospect_clients.src.repositories.user_repository import UserRepository

        client.post("/users/", json={"email": email, "password": "pass"})
        token = client.post(
            "/users/login", data={"username": email, "password": "pass"}
        ).json()["access_token"]
        user = UserRepository(db).get_by_email(email)
        if leads:
            client.post(
                f"/leads/?user_id={user.id_person}",
                json=leads,
                headers={"X-Service-Key": SERVICE_API_KEY},
            )
        return token

    def test_create_leads_endpoint(self, client, db):
        # POST /leads is now a service-to-service endpoint: X-Service-Key + user_id.
        from prospect_clients.src.configurations.auth import SERVICE_API_KEY
        from prospect_clients.src.repositories.user_repository import UserRepository

        user = UserRepository(db).create(email="leadsvc@test.com", hashed_password="h")
        response = client.post(
            f"/leads/?user_id={user.id_person}",
            json=[
                {"nome": "Endpoint Lead", "telefone": "999"},
                {"nome": "Endpoint Lead 2", "telefone": "888"},
            ],
            headers={"X-Service-Key": SERVICE_API_KEY},
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 2

    def test_create_leads_without_service_key(self, client):
        response = client.post("/leads/?user_id=1", json=[{"nome": "No Auth"}])
        assert response.status_code == 401

    def test_list_leads_paginated_shape(self, client, db):
        token = self._seed(
            client,
            db,
            "page@test.com",
            [
                {"nome": "Page Lead 1", "telefone": "1", "categoria": "padaria"},
                {"nome": "Page Lead 2", "telefone": "2", "categoria": "barbearia"},
            ],
        )
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/leads/", params={"skip": 0, "limit": 1}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["skip"] == 0
        assert data["limit"] == 1
        assert len(data["items"]) == 1
        assert "id_lead" in data["items"][0]

    def test_list_leads_filter(self, client, db):
        token = self._seed(
            client,
            db,
            "filter@test.com",
            [
                {"nome": "Filtro Padaria", "categoria": "padaria"},
                {"nome": "Filtro Barbearia", "categoria": "barbearia"},
            ],
        )
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/leads/", params={"categoria": "padaria"}, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["nome"] == "Filtro Padaria"

    def test_list_categories(self, client, db):
        token = self._seed(
            client,
            db,
            "cat@test.com",
            [
                {"nome": "Cat Lead 1", "categoria": "padaria"},
                {"nome": "Cat Lead 2", "categoria": "barbearia"},
                {"nome": "Cat Lead 3", "categoria": "padaria"},
                {"nome": "Cat Lead 4", "categoria": None},
            ],
        )
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/leads/categories", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Distintas, sem None, ordenadas
        assert data == ["barbearia", "padaria"]


class TestOperationLeads:
    """GET /operations/{id}/leads: what a given run collected."""

    def _login(self, client, email):
        client.post("/users/", json={"email": email, "password": "pass"})
        return client.post(
            "/users/login", data={"username": email, "password": "pass"}
        ).json()["access_token"]

    def _user_id(self, db, email):
        return UserRepository(db).get_by_email(email).id_person

    def _create_operation(self, client, token, name="Run"):
        response = client.post(
            "/operations/",
            json={"operation_name": name, "search_text": name, "source": "maps"},
            headers={"Authorization": f"Bearer {token}"},
        )
        return response.json()["id_operation"]

    def _post_leads(self, client, db, email, leads, operation_id=None):
        from prospect_clients.src.configurations.auth import SERVICE_API_KEY

        params = {"user_id": self._user_id(db, email)}
        if operation_id is not None:
            params["operation_id"] = operation_id
        client.post(
            "/leads/",
            params=params,
            json=leads,
            headers={"X-Service-Key": SERVICE_API_KEY},
        )

    def test_returns_only_the_leads_of_that_operation(self, client, db):
        email = "ops@test.com"
        token = self._login(client, email)
        first = self._create_operation(client, token, "Primeira")
        second = self._create_operation(client, token, "Segunda")

        self._post_leads(client, db, email, [{"nome": "Lead A"}], first)
        self._post_leads(client, db, email, [{"nome": "Lead B"}], second)

        response = client.get(
            f"/operations/{first}/leads",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert [lead["nome"] for lead in response.json()] == ["Lead A"]

    def test_leads_posted_without_an_operation_belong_to_none(self, client, db):
        email = "noop@test.com"
        token = self._login(client, email)
        operation = self._create_operation(client, token)

        self._post_leads(client, db, email, [{"nome": "Solto"}])

        response = client.get(
            f"/operations/{operation}/leads",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.json() == []

    def test_another_user_cannot_read_the_run(self, client, db):
        owner = "owner@test.com"
        owner_token = self._login(client, owner)
        operation = self._create_operation(client, owner_token)
        self._post_leads(client, db, owner, [{"nome": "Privado"}], operation)

        intruder_token = self._login(client, "intruder@test.com")
        response = client.get(
            f"/operations/{operation}/leads",
            headers={"Authorization": f"Bearer {intruder_token}"},
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_requires_authentication(self, client):
        assert client.get("/operations/1/leads").status_code in (401, 403)


class TestLeadStats:
    """GET /leads/stats: aggregates counted over the whole base."""

    def _seed(self, client, db, email, leads):
        from prospect_clients.src.configurations.auth import SERVICE_API_KEY

        client.post("/users/", json={"email": email, "password": "pass"})
        token = client.post(
            "/users/login", data={"username": email, "password": "pass"}
        ).json()["access_token"]
        user = UserRepository(db).get_by_email(email)
        client.post(
            "/leads/",
            params={"user_id": user.id_person},
            json=leads,
            headers={"X-Service-Key": SERVICE_API_KEY},
        )
        return token

    def test_counts_the_whole_base_not_one_page(self, client, db):
        # The bug this endpoint exists to fix: the dashboard counted the loaded
        # page, so it showed the page size instead of the real total.
        leads = [{"nome": f"Lead {i}", "telefone": "1"} for i in range(120)]
        token = self._seed(client, db, "stats@test.com", leads)

        body = client.get(
            "/leads/stats", headers={"Authorization": f"Bearer {token}"}
        ).json()

        assert body["total"] == 120

    def test_groups_by_source_and_category(self, client, db):
        token = self._seed(
            client,
            db,
            "grupos@test.com",
            [
                {"nome": "A", "categoria": "Barbearia", "origem": "maps"},
                {"nome": "B", "categoria": "Barbearia", "origem": "maps"},
                {"nome": "@c", "categoria": "Barbearia", "origem": "instagram"},
                {"nome": "D", "categoria": "Pet shop", "origem": "maps"},
            ],
        )

        body = client.get(
            "/leads/stats", headers={"Authorization": f"Bearer {token}"}
        ).json()

        assert {r["origem"]: r["total"] for r in body["por_origem"]} == {
            "maps": 3,
            "instagram": 1,
        }
        # Biggest first.
        assert body["por_categoria"][0] == {"categoria": "Barbearia", "total": 3}
        assert body["total_categorias"] == 2

    def test_counts_missing_contact_details(self, client, db):
        token = self._seed(
            client,
            db,
            "faltando@test.com",
            [
                {"nome": "Completo", "telefone": "1", "site": "a.com"},
                {"nome": "So telefone", "telefone": "1"},
                {"nome": "So site", "site": "b.com"},
                {"nome": "Nada"},
                {"nome": "Vazio", "telefone": "", "site": ""},
            ],
        )

        body = client.get(
            "/leads/stats", headers={"Authorization": f"Bearer {token}"}
        ).json()

        assert body["sem_site"] == 3
        assert body["sem_telefone"] == 3
        # Neither phone nor site: empty strings count as missing, not as filled.
        assert body["sem_contato"] == 2

    def test_one_user_does_not_see_another_users_base(self, client, db):
        self._seed(client, db, "dono@test.com", [{"nome": "Do dono"}])
        outro = self._seed(client, db, "outro@test.com", [{"nome": "Do outro"}])

        body = client.get(
            "/leads/stats", headers={"Authorization": f"Bearer {outro}"}
        ).json()

        assert body["total"] == 1

    def test_requires_authentication(self, client):
        assert client.get("/leads/stats").status_code in (401, 403)
