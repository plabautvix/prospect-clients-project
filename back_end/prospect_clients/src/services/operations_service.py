from fastapi import HTTPException

from prospect_clients.src.repositories.operations_repository import OperationsRepository
from prospect_clients.src.models.schemas.operations import OperationCreate


class OperationsService:
    def __init__(self, repository: OperationsRepository):
        self.repository = repository

    def get_operations(self, user_id: int):
        return self.repository.get_by_user(user_id)

    def create_operation(self, data: OperationCreate, user_id: int):
        return self.repository.create(
            operation_name=data.operation_name,
            search_text=data.search_text,
            status=1,
            id_user=user_id,
            message_for_lead=data.message_for_lead,
        )

    def update_status(self, operation_id: int, status: int):
        operation = self.repository.update_status(operation_id, status)
        if not operation:
            raise HTTPException(status_code=404, detail="Operacao nao encontrada.")
        return operation

    def mark_stopped(self, operation_id: int):
        """Mark an operation as stopped (status=0), best-effort.

        Unlike update_status, this does not raise when the operation is
        missing: stopping an operation must stay idempotent so the UI can
        reflect the stop without failing on already-gone operations.
        """
        return self.repository.update_status(operation_id, 0)

    def get_operation(self, operation_id: int):
        operation = self.repository.get_by_id(operation_id)
        if not operation:
            raise HTTPException(status_code=404, detail="Operacao nao encontrada.")
        return operation

    def reset_orphaned_operations(self) -> int:
        """Reconcile orphaned active operations on startup.

        After an application restart no scraping thread survives, so every
        operation with status=1 is actually stopped and must be marked as
        status=0.
        """
        return self.repository.reset_active_operations()
