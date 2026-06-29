from prospect_clients.src.repositories.user_repository import UserRepository
from prospect_clients.src.services.user_service import UserService


class TestUserRepository:
    def test_create_and_get_by_email(self, db):
        repo = UserRepository(db)
        user = repo.create(email="test@example.com", hashed_password="hashed123")

        assert user.email == "test@example.com"
        assert user.id_person is not None

        found = repo.get_by_email("test@example.com")
        assert found is not None
        assert found.id_person == user.id_person

    def test_get_by_email_not_found(self, db):
        repo = UserRepository(db)
        assert repo.get_by_email("nonexistent@example.com") is None

    def test_get_by_id(self, db):
        repo = UserRepository(db)
        user = repo.create(email="id@test.com", hashed_password="hashed")

        found = repo.get_by_id(user.id_person)
        assert found is not None
        assert found.email == "id@test.com"


class TestUserService:
    def test_register(self, db):
        service = UserService(UserRepository(db))
        from prospect_clients.src.models.schemas.user import UserCreate

        result = service.register(UserCreate(email="new@test.com", password="secret123"))

        assert result.email == "new@test.com"
        assert result.password == "secret123"

        # Verify password was hashed in DB
        repo = UserRepository(db)
        user_in_db = repo.get_by_email("new@test.com")
        assert user_in_db.hashed_password != "secret123"

    def test_authenticate_success(self, db):
        service = UserService(UserRepository(db))
        from prospect_clients.src.models.schemas.user import UserCreate

        service.register(UserCreate(email="auth@test.com", password="mypassword"))
        result = service.authenticate("auth@test.com", "mypassword")

        assert "access_token" in result
        assert result["token_type"] == "bearer"

    def test_token_has_expiration(self, db):
        import jwt
        from prospect_clients.src.configurations.auth import JWT_ALGORITHM, JWT_SECRET
        from prospect_clients.src.models.schemas.user import UserCreate

        service = UserService(UserRepository(db))
        service.register(UserCreate(email="exp@test.com", password="pass"))
        token = service.authenticate("exp@test.com", "pass")["access_token"]

        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert "exp" in payload

    def test_authenticate_wrong_password(self, db):
        service = UserService(UserRepository(db))
        from prospect_clients.src.models.schemas.user import UserCreate
        import pytest

        service.register(UserCreate(email="wrong@test.com", password="correct"))

        with pytest.raises(Exception):
            service.authenticate("wrong@test.com", "incorrect")

    def test_authenticate_user_not_found(self, db):
        service = UserService(UserRepository(db))
        import pytest

        with pytest.raises(Exception):
            service.authenticate("ghost@test.com", "password")

    def test_get_current_user_info(self, db):
        service = UserService(UserRepository(db))
        from prospect_clients.src.models.schemas.user import UserCreate

        service.register(UserCreate(email="me@test.com", password="pass"))
        user = UserRepository(db).get_by_email("me@test.com")

        info = service.get_current_user_info(user.id_person)
        assert info.email == "me@test.com"
        assert info.password == "********"


class TestUserEndpoints:
    def test_create_user_endpoint(self, client):
        response = client.post(
            "/users/",
            json={"email": "endpoint@test.com", "password": "pass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "endpoint@test.com"

    def test_login_endpoint(self, client):
        client.post("/users/", json={"email": "login@test.com", "password": "pass123"})

        response = client.post(
            "/users/login",
            data={"username": "login@test.com", "password": "pass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_userme_endpoint(self, client):
        client.post("/users/", json={"email": "me@test.com", "password": "pass123"})
        login = client.post(
            "/users/login",
            data={"username": "me@test.com", "password": "pass123"},
        )
        token = login.json()["access_token"]

        response = client.get(
            "/users/userme", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == "me@test.com"
        assert response.json()["password"] == "********"

    def test_login_wrong_password(self, client):
        client.post("/users/", json={"email": "fail@test.com", "password": "correct"})

        response = client.post(
            "/users/login",
            data={"username": "fail@test.com", "password": "wrong"},
        )
        assert response.status_code == 400

    def test_userme_invalid_token_returns_401(self, client):
        response = client.get(
            "/users/userme", headers={"Authorization": "Bearer not-a-valid-token"}
        )
        assert response.status_code == 401

    def test_userme_expired_token_returns_401(self, client):
        import jwt
        from datetime import datetime, timedelta, timezone
        from prospect_clients.src.configurations.auth import JWT_ALGORITHM, JWT_SECRET

        expired = jwt.encode(
            {"user_id": 1, "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )
        response = client.get(
            "/users/userme", headers={"Authorization": f"Bearer {expired}"}
        )
        assert response.status_code == 401
