from http import HTTPStatus

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.security import OAuth2PasswordRequestForm

from prospect_clients.src.configurations.auth import PASSWORD_RESET_EXPIRATION_MINUTES
from prospect_clients.src.configurations.dependencies import service_provider
from prospect_clients.src.utils import emails
from prospect_clients.src.utils.mailer import send_email
from prospect_clients.src.utils.security import get_current_user
from prospect_clients.src.models.schemas.user import (
    ForgotPasswordRequest,
    MessageResponse,
    ResetPasswordRequest,
    UserCreate,
    UserPublic,
    UserRegister,
)
from prospect_clients.src.repositories.user_repository import UserRepository
from prospect_clients.src.services.user_service import UserService

router = APIRouter(tags=["users"])

_get_service = service_provider(UserService, UserRepository)

FORGOT_PASSWORD_ANSWER = (
    "Se houver uma conta com este e-mail, enviamos um link para redefinir a senha."
)


@router.post(
    "/",
    status_code=HTTPStatus.CREATED,
    response_model=UserPublic,
    summary="Create a new user",
    description="Sign-up. Answers 409 when the e-mail already has an account.",
)
def create_user(user: UserRegister, service: UserService = Depends(_get_service)):
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


@router.post(
    "/password/forgot",
    status_code=HTTPStatus.ACCEPTED,
    response_model=MessageResponse,
    summary="E-mail a link to set a new password",
    description=(
        "Always answers the same, whether the e-mail has an account or not. "
        "The e-mail goes out after the response."
    ),
)
def forgot_password(
    data: ForgotPasswordRequest,
    background: BackgroundTasks,
    service: UserService = Depends(_get_service),
):
    reset = service.request_password_reset(data.email)
    if reset:
        subject, text, html = emails.password_reset(
            reset.link, PASSWORD_RESET_EXPIRATION_MINUTES
        )
        background.add_task(send_email, reset.email, subject, text, html)
    return MessageResponse(message=FORGOT_PASSWORD_ANSWER)


@router.post(
    "/password/reset",
    response_model=MessageResponse,
    summary="Set a new password with the link from the e-mail",
)
def reset_password(
    data: ResetPasswordRequest, service: UserService = Depends(_get_service)
):
    service.reset_password(data.token, data.password)
    return MessageResponse(message="Senha redefinida. Entre com a nova senha.")
