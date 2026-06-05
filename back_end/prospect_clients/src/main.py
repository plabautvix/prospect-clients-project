import logging
from contextlib import asynccontextmanager

from prospect_clients.src.configurations.database import engine
from prospect_clients.src.models.tables.base import Base
from prospect_clients.src.controllers.automations_controller import router as automations_router
from prospect_clients.src.controllers.user_controller import router as users_router
from prospect_clients.src.controllers.leads_controller import router as leads_router
from prospect_clients.src.controllers.operations_controller import router as operations_router
from prospect_clients.src.repositories.operations_repository import OperationsRepository
from prospect_clients.src.services.operations_service import OperationsService
from sqlalchemy.orm import Session
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Reconcile orphaned operations: after a restart no scraping thread
    # survives, so any status=1 operation in the database is actually stopped.
    db = Session(bind=engine)
    try:
        service = OperationsService(OperationsRepository(db))
        reset = service.reset_orphaned_operations()
        if reset:
            logger.info("Reset %d orphaned active operation(s) on startup", reset)
    finally:
        db.close()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(automations_router, prefix="/automations", tags=["automations", "selenium"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(leads_router)
app.include_router(operations_router)
