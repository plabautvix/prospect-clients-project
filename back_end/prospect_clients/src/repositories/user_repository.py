from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from prospect_clients.src.models.tables.user import PasswordResetToken, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, email: str, hashed_password: str) -> User:
        db_user = User(email=email, hashed_password=hashed_password)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_by_email(self, email: str) -> User | None:
        # Case-insensitive: accounts created before e-mails were lowercased
        # keep working, and "Ana@x.com" cannot sign up next to "ana@x.com".
        return (
            self.db.query(User)
            .filter(func.lower(User.email) == email.strip().lower())
            .first()
        )

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id_person == user_id).first()

    def rollback(self) -> None:
        self.db.rollback()

    def save(self) -> None:
        self.db.commit()

    # ─── Password reset ──────────────────────────────────────────────────────

    def add_reset_token(self, token: PasswordResetToken) -> None:
        self.db.add(token)
        self.db.commit()

    def get_reset_token(self, token_hash: str) -> PasswordResetToken | None:
        return (
            self.db.query(PasswordResetToken)
            .filter(PasswordResetToken.token_hash == token_hash)
            .first()
        )

    def expire_reset_tokens(self, user_id: int, now: datetime) -> None:
        """Mark every pending link of the user as used. Does not commit."""
        (
            self.db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.id_person == user_id,
                PasswordResetToken.used_at.is_(None),
            )
            .update({PasswordResetToken.used_at: now}, synchronize_session=False)
        )
