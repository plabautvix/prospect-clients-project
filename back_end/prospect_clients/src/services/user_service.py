import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from prospect_clients.src.configurations.auth import (
    APP_URL,
    JWT_ALGORITHM,
    JWT_EXPIRATION_MINUTES,
    JWT_SECRET,
    PASSWORD_RESET_EXPIRATION_MINUTES,
)
from prospect_clients.src.models.schemas.user import (
    UserCreate,
    UserPublic,
    UserRegister,
)
from prospect_clients.src.models.tables.user import PasswordResetToken
from prospect_clients.src.repositories.user_repository import UserRepository
from prospect_clients.src.services.pacing import utcnow

# Checked against when the e-mail has no account, so a login takes as long
# either way and its timing does not tell which e-mails are registered.
_DUMMY_HASH = bcrypt.hashpw(b"no-such-user", bcrypt.gensalt())

INVALID_LOGIN = "E-mail ou senha incorretos."
INVALID_RESET_LINK = "Este link de redefinicao e invalido ou expirou. Peca um novo."


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PasswordResetLink:
    email: str
    link: str


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def register(self, user_data: UserRegister) -> UserPublic:
        email = user_data.email.strip().lower()
        duplicate = HTTPException(
            status_code=409, detail="Ja existe uma conta com este e-mail."
        )
        if self.repository.get_by_email(email):
            raise duplicate

        try:
            self.repository.create(
                email=email, hashed_password=_hash_password(user_data.password)
            )
        except IntegrityError:
            # Two sign-ups with the same e-mail at the same time.
            self.repository.rollback()
            raise duplicate

        return UserPublic(email=email)

    def authenticate(self, email: str, password: str) -> dict:
        user = self.repository.get_by_email(email)
        # The same answer whether the e-mail or the password is wrong, so the
        # login form cannot be used to find out who has an account.
        stored = user.hashed_password.encode("utf-8") if user else _DUMMY_HASH
        if not bcrypt.checkpw(password.encode("utf-8"), stored) or not user:
            raise HTTPException(status_code=400, detail=INVALID_LOGIN)

        expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRATION_MINUTES)
        token = jwt.encode(
            {"user_id": user.id_person, "exp": expire},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )

        return {"access_token": token, "token_type": "bearer"}

    def get_current_user_info(self, user_id: int) -> UserCreate:
        user = self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=400, detail="Usuario nao encontrado.")

        return UserCreate(email=user.email, password="********")

    # ─── Password reset ──────────────────────────────────────────────────────

    def request_password_reset(self, email: str) -> PasswordResetLink | None:
        """Create a reset link, or None when the e-mail has no account.

        The caller answers the same in both cases and sends the e-mail in the
        background, so neither the response nor its timing gives anything away.
        """
        user = self.repository.get_by_email(email)
        if user is None:
            return None

        now = utcnow()
        # Only the newest link works: asking again makes the old ones useless.
        self.repository.expire_reset_tokens(user.id_person, now)

        token = secrets.token_urlsafe(32)
        self.repository.add_reset_token(
            PasswordResetToken(
                id_person=user.id_person,
                token_hash=_hash_token(token),
                created_at=now,
                expires_at=now + timedelta(minutes=PASSWORD_RESET_EXPIRATION_MINUTES),
            )
        )
        return PasswordResetLink(
            email=user.email, link=f"{APP_URL}/redefinir-senha?token={token}"
        )

    def reset_password(self, token: str, password: str) -> None:
        now = utcnow()
        reset = self.repository.get_reset_token(_hash_token(token))
        if reset is None or reset.used_at is not None or reset.expires_at <= now:
            raise HTTPException(status_code=400, detail=INVALID_RESET_LINK)

        user = self.repository.get_by_id(reset.id_person)
        user.hashed_password = _hash_password(password)
        # Spends this link and any other still pending.
        self.repository.expire_reset_tokens(user.id_person, now)
        self.repository.save()
