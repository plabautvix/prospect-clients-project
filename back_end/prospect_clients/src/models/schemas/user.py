from pydantic import BaseModel, EmailStr, Field, field_validator

# bcrypt only reads the first 72 bytes and the library refuses longer input.
PASSWORD_MAX_BYTES = 72


def _check_password(value: str) -> str:
    if len(value.encode("utf-8")) > PASSWORD_MAX_BYTES:
        raise ValueError("A senha pode ter no maximo 72 bytes.")
    return value


class UserCreate(BaseModel):
    email: str
    password: str

    model_config = {
        "json_schema_extra": {
            "example":  {
                "email": "user@example.com",
                "password": "strongpassword123"
            }
        }
    }


class UserRegister(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=8)

    _password_bytes = field_validator("password")(_check_password)

    model_config = {
        "json_schema_extra": {
            "example": {"email": "voce@empresa.com", "password": "uma-senha-forte"}
        }
    }


class UserPublic(BaseModel):
    email: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=200)
    password: str = Field(..., min_length=8)

    _password_bytes = field_validator("password")(_check_password)


class MessageResponse(BaseModel):
    message: str
