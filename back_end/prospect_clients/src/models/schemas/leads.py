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


class OrigemCount(BaseModel):
    origem: str
    total: int


class CategoriaCount(BaseModel):
    categoria: str
    total: int


class LeadsStats(BaseModel):
    """Aggregates for the dashboard, counted over the user's whole base."""

    total: int = Field(..., description="Leads the user has collected.")
    por_origem: List[OrigemCount] = Field(..., description="Count per source.")
    por_categoria: List[CategoriaCount] = Field(
        ..., description="Count per category, biggest first."
    )
    total_categorias: int = Field(..., description="Distinct categories.")
    sem_site: int = Field(..., description="Leads with no website.")
    sem_telefone: int = Field(..., description="Leads with no phone.")
    sem_endereco: int = Field(..., description="Leads with no address.")
    sem_contato: int = Field(
        ..., description="Leads with neither phone nor website: unreachable."
    )
