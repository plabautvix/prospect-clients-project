from sqlalchemy.orm import Session

from prospect_clients.src.models.tables.operations import Operations


class OperationsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, operation_name: str, search_text: str, status: int,
               id_user: int, message_for_lead: str | None = None,
               source: str = "maps") -> Operations:
        operation = Operations(
            operation_name=operation_name,
            search_text=search_text,
            status=status,
            id_user=id_user,
            message_for_lead=message_for_lead,
            source=source,
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

    def get_by_user(self, user_id: int) -> list[Operations]:
        return (
            self.db.query(Operations)
            .filter(Operations.id_user == user_id)
            .order_by(Operations.id_operation.desc())
            .all()
        )

    def update_status(self, operation_id: int, status: int) -> Operations | None:
        operation = self.get_by_id(operation_id)
        if operation:
            operation.status = status
            self.db.commit()
            self.db.refresh(operation)
        return operation

    def reset_active_operations(self) -> int:
        """Mark every active operation (status=1) as stopped (status=0).

        Used on backend startup: after an application restart no scraping
        thread survives, so operations left as active in the database are
        orphaned and must be reconciled.
        """
        updated = (
            self.db.query(Operations)
            .filter(Operations.status == 1)
            .update({Operations.status: 0})
        )
        self.db.commit()
        return updated
