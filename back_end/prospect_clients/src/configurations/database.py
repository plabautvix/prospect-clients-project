from sqlalchemy import create_engine
from sqlalchemy.orm import Session


DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=True)


def get_db():
    db = Session(bind=engine)
    try:
        yield db
    finally:
        db.close()
