from pydantic import BaseModel


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
