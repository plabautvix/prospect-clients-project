from datetime import datetime
from .base import Base
from sqlalchemy import ForeignKey, DateTime
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
    """
    __tablename__ = "leads"
    id_lead: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    telefone: Mapped[str] = mapped_column(String(50), nullable=True)
    endereco: Mapped[str] = mapped_column(String(255), nullable=True)
    site: Mapped[str] = mapped_column(String(255), nullable=True)
    foto: Mapped[str] = mapped_column(String(255), nullable=True)
    categoria: Mapped[str] = mapped_column(String(100), nullable=True)


class UserLeadHistory(Base):
    __tablename__ = "user_lead_history"

    id_lead_history: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id_person"), nullable=False)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id_lead"), nullable=False)
    encontrado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
