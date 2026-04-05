import bcrypt
import jwt
from fastapi import HTTPException

from prospect_clients.src.repositories.user_repository import UserRepository
from prospect_clients.src.models.schemas.user import UserCreate

JWT_SECRET = "euvouvencer"
JWT_ALGORITHM = "HS256"


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def register(self, user_data: UserCreate) -> UserCreate:
        hashed_password = bcrypt.hashpw(
            user_data.password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        self.repository.create(email=user_data.email, hashed_password=hashed_password)

        return UserCreate(email=user_data.email, password=user_data.password)

    def authenticate(self, email: str, password: str) -> dict:
        user = self.repository.get_by_email(email)
        if not user:
            raise HTTPException(status_code=400, detail="Usuario nao encontrado.")

        if not bcrypt.checkpw(password.encode("utf-8"), user.hashed_password.encode("utf-8")):
            raise HTTPException(status_code=400, detail="Senha incorreta.")

        token = jwt.encode(
            {"user_id": user.id_person}, JWT_SECRET, algorithm=JWT_ALGORITHM
        )

        return {"access_token": token, "token_type": "bearer"}

    def get_current_user_info(self, user_id: int) -> UserCreate:
        user = self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=400, detail="Usuario nao encontrado.")

        return UserCreate(email=user.email, password="********")
