import sys
from unittest.mock import MagicMock

# Mock paho.mqtt before any app import tries to connect to broker
mqtt_mock = MagicMock()
sys.modules["paho"] = mqtt_mock
sys.modules["paho.mqtt"] = mqtt_mock
sys.modules["paho.mqtt.client"] = mqtt_mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from prospect_clients.src.models.tables.base import Base
from prospect_clients.src.configurations.database import get_db
from prospect_clients.src.main import app

engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine_test)
    session = Session(bind=engine_test)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine_test)


@pytest.fixture()
def client(db):
    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
