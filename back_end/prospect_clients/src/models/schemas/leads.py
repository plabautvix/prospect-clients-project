from pydantic import BaseModel, Field
from typing import Optional

from sqlalchemy import Integer


class LeadSchema(BaseModel):
    nome: str = Field(..., description="The name of the lead.")
    telefone: Optional[str] = Field(None, description="The phone number of the lead.")
    endereco: Optional[str] = Field(None, description="The address of the lead.")
    site: Optional[str] = Field(None, description="The website of the lead.")
    foto: Optional[str] = Field(None, description="The photo URL of the lead.")
    categoria: Optional[str] = Field(None, description="The category of the lead.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "nome": "Lead Example",
                "telefone": "+1234567890",
                "endereco": "123 Example St, City, Country",
                "site": "https://www.example.com",
                "foto": "https://www.example.com/photo.jpg",
                "categoria": "Example Category"
            }
        }
    }