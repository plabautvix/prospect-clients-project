from typing import Callable, TypeVar

from fastapi import Depends
from sqlalchemy.orm import Session

from prospect_clients.src.configurations.database import get_db

ServiceT = TypeVar("ServiceT")


def service_provider(
    service_cls: type[ServiceT], repository_cls: type
) -> Callable[..., ServiceT]:
    """Build a FastAPI dependency provider for a service.

    Takes the service and repository classes and returns a dependency
    function. The `db` is resolved per request via Depends(get_db) and
    injected on construction: service_cls(repository_cls(db)).

    Usage:
        _get_service = service_provider(LeadsService, LeadsRepository)
    """

    def _provider(db: Session = Depends(get_db)) -> ServiceT:
        return service_cls(repository_cls(db))

    return _provider
