from fastapi import APIRouter, Depends, HTTPException
import bcrypt
from sqlalchemy.orm import Session
import jwt
from prospect_clients.src.configurations.database import get_db
from prospect_clients.src.models.schemas.user import UserCreate
from prospect_clients.src.models.tables.user import User
router = APIRouter(tags=["users"])


@router.post("/", response_model=UserCreate)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password: bytes = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
    user.password = hashed_password.decode('utf-8')
    db_user = User(email=user.email, hashed_password=user.password)
    db.add(db_user)
    db.commit()
    return user


@router.post("/login")
def login_user(user: UserCreate, db: Session = Depends(get_db)):
    user_returned = db.query(User).filter(
        User.email == user.email
    ).first()

    if not user_returned:
        raise HTTPException(status_code=400, detail="Usuário não encontrado.")
    

    if not bcrypt.checkpw(user.password.encode("utf-8"), user_returned.hashed_password.encode("utf-8")):
        raise HTTPException(status_code=400, detail="Senha incorreta.")

    encoded_jwt = jwt.encode(
        {"user_id": user_returned.id_person},
        "euvouvencer",
        algorithm="HS256"
    )

    return {
        "access_token": encoded_jwt,
        "token_type": "bearer"
    }
