from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
import bcrypt
from sqlalchemy.orm import Session
import jwt
from prospect_clients.src.configurations.database import get_db
from prospect_clients.src.utils.security import get_current_user
from prospect_clients.src.models.schemas.user import UserCreate
from prospect_clients.src.models.tables.user import User
router = APIRouter(tags=["users"])


@router.post("/", response_model=UserCreate, summary="Create a new user", description="This endpoint creates a new user in the database.")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    This function creates a new user in the database.

    Args:
        user (UserCreate): The user data to be created.
        db (Session): The database session.
    
    Returns:
        UserCreate: The created user data.
    """
    hashed_password: bytes = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
    user.password = hashed_password.decode('utf-8')
    db_user = User(email=user.email, hashed_password=user.password)
    db.add(db_user)
    db.commit()
    return user


@router.post("/login", summary="User login", description="This endpoint allows a user to log in and receive a JWT token.")
def login_user(user: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user_returned = db.query(User).filter(
        User.email == user.username
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

@router.get("/userme", response_model=UserCreate, summary="Get current user", description="This endpoint retrieves the current authenticated user's information.")
def get_current_user_info(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    This function retrieves the current authenticated user's information.

    Args:
        current_user (dict): The current authenticated user.
        db (Session): The database session.
    
    Returns:
        UserCreate: The current user's data.
    """
    user_returned = db.query(User).filter(
        User.id_person == current_user["user_id"]
    ).first()

    if not user_returned:
        raise HTTPException(status_code=400, detail="Usuário não encontrado.")

    return UserCreate(email=user_returned.email, password="********")
