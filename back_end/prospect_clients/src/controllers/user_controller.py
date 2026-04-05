from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from prospect_clients.src.configurations.database import get_db
from prospect_clients.src.utils.security import get_current_user
from prospect_clients.src.models.schemas.user import UserCreate
from prospect_clients.src.repositories.user_repository import UserRepository
from prospect_clients.src.services.user_service import UserService

router = APIRouter(tags=["users"])


def _get_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


@router.post(
    "/",
    response_model=UserCreate,
    summary="Create a new user",
    description="This endpoint creates a new user in the database.",
)
def create_user(user: UserCreate, service: UserService = Depends(_get_service)):
    return service.register(user)


@router.post(
    "/login",
    summary="User login",
    description="This endpoint allows a user to log in and receive a JWT token.",
)
def login_user(
    form: OAuth2PasswordRequestForm = Depends(),
    service: UserService = Depends(_get_service),
):
    return service.authenticate(email=form.username, password=form.password)


@router.get(
    "/userme",
    response_model=UserCreate,
    summary="Get current user",
    description="This endpoint retrieves the current authenticated user's information.",
)
def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(_get_service),
):
    return service.get_current_user_info(current_user["user_id"])
