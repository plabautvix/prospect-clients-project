from sqlalchemy.orm import Session

from prospect_clients.src.models.tables.user import User


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
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id_person == user_id).first()
