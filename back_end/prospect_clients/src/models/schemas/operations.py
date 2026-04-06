from pydantic import BaseModel, Field
from typing import Optional


class OperationCreate(BaseModel):
    operation_name: str = Field(..., description="Name of the operation")
    search_text: str = Field(..., description="Search text used for scraping")
    message_for_lead: Optional[str] = Field(None, description="Message template for leads")

    model_config = {
        "json_schema_extra": {
            "example": {
                "operation_name": "Pizzarias SP",
                "search_text": "pizzarias em Sao Paulo",
                "message_for_lead": "Ola {nome}, tudo bem?"
            }
        }
    }


class OperationResponse(BaseModel):
    id_operation: int
    operation_name: str
    search_text: str
    message_for_lead: Optional[str] = None
    status: int
    id_user: Optional[int] = None

    class Config:
        from_attributes = True


class OperationStatusUpdate(BaseModel):
    status: int = Field(..., description="New status (0=inactive, 1=active)")
