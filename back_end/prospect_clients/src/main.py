from prospect_clients.src.configurations.database import engine
from prospect_clients.src.models.tables.user import Base
from prospect_clients.src.routes.automations import router as automations_router
from prospect_clients.src.routes.user import router as users_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
Base.metadata.create_all(bind=engine)
app.include_router(automations_router, prefix="/automations", tags=["automations", "selenium"])
app.include_router(users_router, prefix="/users", tags=["users"])
