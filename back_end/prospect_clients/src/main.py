from prospect_clients.src.configurations.database import engine
from prospect_clients.src.models.tables.base import Base
from prospect_clients.src.controllers.automations_controller import router as automations_router
from prospect_clients.src.controllers.user_controller import router as users_router
from prospect_clients.src.controllers.leads_controller import router as leads_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI()
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
