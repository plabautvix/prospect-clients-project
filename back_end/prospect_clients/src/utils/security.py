import jwt
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, "euvouvencer", algorithms=["HS256"])
        user_id: int = payload.get("user_id")
        print("loguei", user_id)
        if user_id is None:
            raise Exception("Invalid token")
        return {"user_id": user_id, "token": token}
    except jwt.PyJWTError:
        raise Exception("Could not validate credentials")
