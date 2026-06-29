import secrets

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer

from prospect_clients.src.configurations.auth import (
    JWT_ALGORITHM,
    JWT_SECRET,
    SERVICE_API_KEY,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")
service_key_header = APIKeyHeader(name="X-Service-Key", auto_error=False)


def require_service(api_key: str | None = Security(service_key_header)) -> bool:
    """Authenticate internal services via the X-Service-Key header.

    Separate from user authentication (get_current_user): services have their own
    credential, validated with a constant-time comparison.
    """
    if not api_key or not secrets.compare_digest(api_key, SERVICE_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing service credentials",
        )
    return True


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise credentials_exception

    user_id = payload.get("user_id")
    if user_id is None:
        raise credentials_exception

    return {"user_id": user_id, "token": token}
