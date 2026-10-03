from datetime import datetime
from .base import Base
from sqlalchemy import Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import Integer, String


class Leads(Base):
    """
    This class represents the 'leads' table in the database.
    It defines the structure of the table and its columns. 
    
    Attributes:
        id_lead (int): The primary key of the lead.
        nome (str): The name of the lead.
        telefone (str): The phone number of the lead.
        endereco (str): The address of the lead.
        site (str): The website of the lead.
        foto (str): The photo URL of the lead.
        origem (str): Which service found it ("maps" or "instagram").
        nao_contatar (bool): The lead asked not to be contacted again. No
            campaign includes it.
    """
    __tablename__ = "leads"
    id_lead: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    telefone: Mapped[str] = mapped_column(String(50), nullable=True)
    endereco: Mapped[str] = mapped_column(String(255), nullable=True)
    site: Mapped[str] = mapped_column(String(255), nullable=True)
    foto: Mapped[str] = mapped_column(String(255), nullable=True)
    categoria: Mapped[str] = mapped_column(String(100), nullable=True)
    origem: Mapped[str] = mapped_column(
        String(20), nullable=False, default="maps", server_default="maps"
    )
    nao_contatar: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )


class UserLeadHistory(Base):
    __tablename__ = "user_lead_history"

    id_lead_history: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id_person"), nullable=False)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id_lead"), nullable=False)
    encontrado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # Which run found it. Null for rows written before this was recorded.
    id_operation: Mapped[int] = mapped_column(
        ForeignKey("operations.id_operation"), nullable=True
    )
