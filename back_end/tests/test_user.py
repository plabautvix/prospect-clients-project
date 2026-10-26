from datetime import timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException

from prospect_clients.src.models.schemas.user import UserRegister
from prospect_clients.src.models.tables.user import PasswordResetToken
from prospect_clients.src.repositories.user_repository import UserRepository
from prospect_clients.src.services.pacing import utcnow
from prospect_clients.src.services.user_service import UserService

SEND_EMAIL = "prospect_clients.src.controllers.user_controller.send_email"


def _register(db, email="user@test.com", password="password123"):
    return UserService(UserRepository(db)).register(
        UserRegister(email=email, password=password)
    )


def _token_from(link: str) -> str:
    return parse_qs(urlparse(link).query)["token"][0]


class TestUserRepository:
    def test_create_and_get_by_email(self, db):
        repo = UserRepository(db)
        user = repo.create(email="test@example.com", hashed_password="hashed123")

        assert user.email == "test@example.com"
        assert user.id_person is not None

        found = repo.get_by_email("test@example.com")
        assert found is not None
        assert found.id_person == user.id_person

    def test_get_by_email_ignores_case(self, db):
        repo = UserRepository(db)
        user = repo.create(email="Mixed@Example.com", hashed_password="hashed")

        assert repo.get_by_email("mixed@example.com").id_person == user.id_person

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
        result = _register(db, "new@test.com", "secret123")

        assert result.email == "new@test.com"
        assert not hasattr(result, "password")

        # Verify password was hashed in DB
        user_in_db = UserRepository(db).get_by_email("new@test.com")
        assert user_in_db.hashed_password != "secret123"

    def test_register_lowercases_the_email(self, db):
        assert _register(db, "Ana@Empresa.com").email == "ana@empresa.com"

    def test_register_duplicate_email_is_a_conflict(self, db):
        _register(db, "dup@test.com")

        with pytest.raises(HTTPException) as error:
            _register(db, "DUP@test.com")
        assert error.value.status_code == 409

    def test_authenticate_success(self, db):
        _register(db, "auth@test.com", "mypassword")
        result = UserService(UserRepository(db)).authenticate(
            "auth@test.com", "mypassword"
        )

        assert "access_token" in result
        assert result["token_type"] == "bearer"

    def test_token_has_expiration(self, db):
        import jwt
        from prospect_clients.src.configurations.auth import JWT_ALGORITHM, JWT_SECRET

        _register(db, "exp@test.com", "password1")
        token = UserService(UserRepository(db)).authenticate(
            "exp@test.com", "password1"
        )["access_token"]

        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert "exp" in payload

    def test_wrong_password_and_unknown_email_get_the_same_answer(self, db):
        service = UserService(UserRepository(db))
        _register(db, "wrong@test.com", "correct-pass")

        with pytest.raises(HTTPException) as wrong_password:
            service.authenticate("wrong@test.com", "incorrect")
        with pytest.raises(HTTPException) as unknown_email:
            service.authenticate("ghost@test.com", "password")

        assert wrong_password.value.status_code == unknown_email.value.status_code == 400
        assert wrong_password.value.detail == unknown_email.value.detail

    def test_get_current_user_info(self, db):
        service = UserService(UserRepository(db))
        _register(db, "me@test.com")
        user = UserRepository(db).get_by_email("me@test.com")

        info = service.get_current_user_info(user.id_person)
        assert info.email == "me@test.com"
        assert info.password == "********"


class TestPasswordReset:
    def test_unknown_email_gets_no_link(self, db):
        service = UserService(UserRepository(db))
        assert service.request_password_reset("ghost@test.com") is None

    def test_only_the_token_hash_is_stored(self, db):
        _register(db, "hash@test.com")
        reset = UserService(UserRepository(db)).request_password_reset("hash@test.com")

        token = _token_from(reset.link)
        stored = db.query(PasswordResetToken).one()
        assert stored.token_hash != token
        assert len(stored.token_hash) == 64

    def test_reset_changes_the_password_once(self, db):
        service = UserService(UserRepository(db))
        _register(db, "reset@test.com", "old-password")
        token = _token_from(service.request_password_reset("reset@test.com").link)

        service.reset_password(token, "new-password")

        assert "access_token" in service.authenticate("reset@test.com", "new-password")
        with pytest.raises(HTTPException):
            service.authenticate("reset@test.com", "old-password")
        # The link is spent.
        with pytest.raises(HTTPException) as error:
            service.reset_password(token, "another-password")
        assert error.value.status_code == 400

    def test_a_new_request_voids_the_previous_link(self, db):
        service = UserService(UserRepository(db))
        _register(db, "twice@test.com")
        first = _token_from(service.request_password_reset("twice@test.com").link)
        second = _token_from(service.request_password_reset("twice@test.com").link)

        with pytest.raises(HTTPException):
            service.reset_password(first, "new-password")
        service.reset_password(second, "new-password")

    def test_expired_link_is_refused(self, db):
        service = UserService(UserRepository(db))
        _register(db, "late@test.com")
        token = _token_from(service.request_password_reset("late@test.com").link)
        stored = db.query(PasswordResetToken).one()
        stored.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()

        with pytest.raises(HTTPException) as error:
            service.reset_password(token, "new-password")
        assert error.value.status_code == 400

    def test_unknown_token_is_refused(self, db):
        with pytest.raises(HTTPException) as error:
            UserService(UserRepository(db)).reset_password("made-up", "new-password")
        assert error.value.status_code == 400


class TestUserEndpoints:
    def test_create_user_endpoint(self, client):
        response = client.post(
            "/users/",
            json={"email": "endpoint@test.com", "password": "pass1234"},
        )
        assert response.status_code == 201
        assert response.json() == {"email": "endpoint@test.com"}

    def test_create_user_duplicate_returns_409(self, client):
        payload = {"email": "twice@test.com", "password": "pass1234"}
        client.post("/users/", json=payload)

        assert client.post("/users/", json=payload).status_code == 409

    @pytest.mark.parametrize(
        "payload",
        [
            {"email": "not-an-email", "password": "pass1234"},
            {"email": "short@test.com", "password": "1234567"},
            {"email": "long@test.com", "password": "x" * 73},
        ],
    )
    def test_create_user_rejects_invalid_input(self, client, payload):
        assert client.post("/users/", json=payload).status_code == 422

    def test_login_endpoint(self, client):
        client.post("/users/", json={"email": "login@test.com", "password": "pass1234"})

        response = client.post(
            "/users/login",
            data={"username": "login@test.com", "password": "pass1234"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_userme_endpoint(self, client):
        client.post("/users/", json={"email": "me@test.com", "password": "pass1234"})
        login = client.post(
            "/users/login",
            data={"username": "me@test.com", "password": "pass1234"},
        )
        token = login.json()["access_token"]

        response = client.get(
            "/users/userme", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == "me@test.com"
        assert response.json()["password"] == "********"

    def test_login_wrong_password(self, client):
        client.post("/users/", json={"email": "fail@test.com", "password": "correct1"})

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
        from datetime import datetime, timezone
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

    def test_forgot_password_answers_the_same_for_any_email(self, client):
        client.post("/users/", json={"email": "known@test.com", "password": "pass1234"})

        with patch(SEND_EMAIL) as send:
            known = client.post("/users/password/forgot", json={"email": "known@test.com"})
            unknown = client.post(
                "/users/password/forgot", json={"email": "unknown@test.com"}
            )

        assert known.status_code == unknown.status_code == 202
        assert known.json() == unknown.json()
        # Only the real account gets an e-mail.
        send.assert_called_once()
        assert send.call_args.args[0] == "known@test.com"

    def test_full_reset_flow(self, client):
        client.post("/users/", json={"email": "flow@test.com", "password": "old-pass1"})
        with patch(SEND_EMAIL) as send:
            client.post("/users/password/forgot", json={"email": "flow@test.com"})
        _, subject, text, html = send.call_args.args
        token = _token_from(text.split("\n\n")[2])
        assert token in html

        response = client.post(
            "/users/password/reset", json={"token": token, "password": "new-pass1"}
        )
        assert response.status_code == 200

        login = client.post(
            "/users/login", data={"username": "flow@test.com", "password": "new-pass1"}
        )
        assert login.status_code == 200

    def test_reset_with_bad_token_returns_400(self, client):
        response = client.post(
            "/users/password/reset", json={"token": "nope", "password": "new-pass1"}
        )
        assert response.status_code == 400
