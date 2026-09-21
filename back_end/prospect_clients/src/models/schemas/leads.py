from pydantic import BaseModel, Field
from typing import List, Optional


class LeadSchema(BaseModel):
    nome: str = Field(..., description="The name of the lead.")
    telefone: Optional[str] = Field(None, description="The phone number of the lead.")
    endereco: Optional[str] = Field(None, description="The address of the lead.")
    site: Optional[str] = Field(None, description="The website of the lead.")
    foto: Optional[str] = Field(None, description="The photo URL of the lead.")
    categoria: Optional[str] = Field(None, description="The category of the lead.")
    origem: str = Field(
        "maps",
        description="Which service found the lead: 'maps' or 'instagram'.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "nome": "Lead Example",
                "telefone": "+1234567890",
                "endereco": "123 Example St, City, Country",
                "site": "https://www.example.com",
                "foto": "https://www.example.com/photo.jpg",
                "categoria": "Example Category",
                "origem": "maps"
            }
        }
    }


class LeadResponse(LeadSchema):
    id_lead: int = Field(..., description="The primary key of the lead.")

    model_config = {"from_attributes": True}


class LeadsPage(BaseModel):
    items: List[LeadResponse] = Field(..., description="Leads in the current page.")
    total: int = Field(..., description="Total number of leads matching the filters.")
    skip: int = Field(..., description="Number of leads skipped (offset).")
    limit: int = Field(..., description="Maximum number of leads per page.")
