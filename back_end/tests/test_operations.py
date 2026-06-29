from prospect_clients.src.repositories.operations_repository import OperationsRepository
from prospect_clients.src.repositories.user_repository import UserRepository
from prospect_clients.src.services.operations_service import OperationsService
from prospect_clients.src.models.schemas.operations import OperationCreate
import pytest


class TestOperationsRepository:
    def test_create_operation(self, db):
        user_repo = UserRepository(db)
        user = user_repo.create(email="op@test.com", hashed_password="hash")

        repo = OperationsRepository(db)
        op = repo.create(
            operation_name="Test Op",
            search_text="pizzarias SP",
            status=1,
            id_user=user.id_person,
            message_for_lead="Ola {nome}",
        )
        assert op.id_operation is not None
        assert op.operation_name == "Test Op"
        assert op.status == 1

    def test_get_by_id(self, db):
        user_repo = UserRepository(db)
        user = user_repo.create(email="op2@test.com", hashed_password="hash")

        repo = OperationsRepository(db)
        op = repo.create("Op2", "barbearias", 1, user.id_person)

        found = repo.get_by_id(op.id_operation)
        assert found is not None
        assert found.search_text == "barbearias"

    def test_update_status(self, db):
        user_repo = UserRepository(db)
        user = user_repo.create(email="op3@test.com", hashed_password="hash")

        repo = OperationsRepository(db)
        op = repo.create("Op3", "lojas", 1, user.id_person)

        updated = repo.update_status(op.id_operation, 0)
        assert updated.status == 0


class TestOperationsService:
    def test_create_operation(self, db):
        user_repo = UserRepository(db)
        user = user_repo.create(email="svc_op@test.com", hashed_password="hash")

        service = OperationsService(OperationsRepository(db))
        op = service.create_operation(
            OperationCreate(operation_name="Svc Op", search_text="cafes"),
            user_id=user.id_person,
        )
        assert op.status == 1
        assert op.operation_name == "Svc Op"

    def test_update_status_not_found(self, db):
        service = OperationsService(OperationsRepository(db))
        with pytest.raises(Exception):
            service.update_status(9999, 0)

    def test_get_operation_not_found(self, db):
        service = OperationsService(OperationsRepository(db))
        with pytest.raises(Exception):
            service.get_operation(9999)


class TestOperationsEndpoints:
    def _get_token(self, client):
        client.post("/users/", json={"email": "ops@test.com", "password": "pass"})
        login = client.post(
            "/users/login", data={"username": "ops@test.com", "password": "pass"}
        )
        return login.json()["access_token"]

    def test_create_operation_endpoint(self, client):
        token = self._get_token(client)
        response = client.post(
            "/operations/",
            json={"operation_name": "Padarias", "search_text": "padarias RJ"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["operation_name"] == "Padarias"
        assert data["status"] == 1
        assert data["id_operation"] is not None

    def test_update_status_endpoint(self, client):
        token = self._get_token(client)
        create = client.post(
            "/operations/",
            json={"operation_name": "Stop Test", "search_text": "lojas"},
            headers={"Authorization": f"Bearer {token}"},
        )
        op_id = create.json()["id_operation"]

        # PATCH status is now service-only (X-Service-Key).
        from prospect_clients.src.configurations.auth import SERVICE_API_KEY

        response = client.patch(
            f"/operations/{op_id}/status",
            json={"status": 0},
            headers={"X-Service-Key": SERVICE_API_KEY},
        )
        assert response.status_code == 200
        assert response.json()["status"] == 0

    def test_get_operation_endpoint(self, client):
        token = self._get_token(client)
        create = client.post(
            "/operations/",
            json={"operation_name": "Get Test", "search_text": "restaurantes"},
            headers={"Authorization": f"Bearer {token}"},
        )
        op_id = create.json()["id_operation"]

        response = client.get(
            f"/operations/{op_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["search_text"] == "restaurantes"

    def test_operations_unauthenticated(self, client):
        response = client.post(
            "/operations/",
            json={"operation_name": "Fail", "search_text": "x"},
        )
        assert response.status_code in (401, 403)
