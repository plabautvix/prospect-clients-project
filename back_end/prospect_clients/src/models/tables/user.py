from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import Integer, String
from .base import Base


class User(Base):
    __tablename__ = "user"

    id_person: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)


class PasswordResetToken(Base):
    """A single-use link to set a new password.

    Only the SHA-256 of the token is kept: whoever reads the database cannot
    use a pending link.
    """

    __tablename__ = "password_reset_tokens"

    id_token: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_person: Mapped[int] = mapped_column(
        ForeignKey("user.id_person"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
