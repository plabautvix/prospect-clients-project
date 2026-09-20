from .base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import Integer, String
from sqlalchemy import ForeignKey

class Operations(Base):
    """
    This class represents the 'operations' table in the database.
    It defines the structure of the table and its columns.

    Attributes:
        id_operation (int): The primary key of the operation.
        operation_name (str): The name of the operation.
        search_text (str): The text used for searching.
        status (int): The status of the operation.
        source (str): Which scraping service runs it ("maps" or "instagram").
    """
    __tablename__ = "operations"

    id_operation: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    operation_name: Mapped[str] = mapped_column(String, nullable=False)
    search_text: Mapped[str] = mapped_column(String, nullable=False)
    message_for_lead: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[int] = mapped_column(Integer, nullable=False)
    id_user: Mapped[int] = mapped_column(ForeignKey("user.id_person"), nullable=True)
    # Tells the frontend which deactivate endpoint to call, so stopping an
    # operation still works after a page reload.
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="maps", server_default="maps"
    )
