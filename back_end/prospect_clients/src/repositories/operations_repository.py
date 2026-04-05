from sqlalchemy.orm import Session

from prospect_clients.src.models.tables.operations import Operations


class OperationsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, operation_name: str, search_text: str, status: int,
               id_user: int, message_for_lead: str | None = None) -> Operations:
        operation = Operations(
            operation_name=operation_name,
            search_text=search_text,
            status=status,
            id_user=id_user,
            message_for_lead=message_for_lead,
        )
        self.db.add(operation)
        self.db.commit()
        self.db.refresh(operation)
        return operation

    def get_by_id(self, operation_id: int) -> Operations | None:
        return (
            self.db.query(Operations)
            .filter(Operations.id_operation == operation_id)
            .first()
        )

    def update_status(self, operation_id: int, status: int) -> Operations | None:
        operation = self.get_by_id(operation_id)
        if operation:
            operation.status = status
            self.db.commit()
            self.db.refresh(operation)
        return operation
