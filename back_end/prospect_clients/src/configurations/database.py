from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=True, poolclass=StaticPool)


def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()
