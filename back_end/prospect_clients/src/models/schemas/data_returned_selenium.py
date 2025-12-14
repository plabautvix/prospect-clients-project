from pydantic import BaseModel, Field
from typing import Optional


class InformationOfLead(BaseModel):
    nome: Optional[str] = Field(None, description="Name of the business or entity")
    endereco: Optional[str] = Field(
        None, description="Address of the business or entity"
    )
    telefone: Optional[str] = Field(
        None, description="Phone number of the business or entity"
    )
    site: Optional[str] = Field(
        None, description="Website URL of the business or entity"
    )
    foto: Optional[str] = Field(
        None, description="URL of the photo of the business or entity"
    )


class LeadsResponse(BaseModel):
    leads: list[InformationOfLead] = Field(
        ..., description="List of leads with their contact information"
    )
    