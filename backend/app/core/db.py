import uuid
import datetime
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import get_settings

import os
import shutil

settings = get_settings()
db_url = settings.effective_database_url

# If serverless /tmp sqlite is used and does not exist yet, copy seeded db
if db_url.startswith("sqlite:////tmp/") and not os.path.exists("/tmp/insightflow.db"):
    potential_sources = [
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "insightflow.db"),
        os.path.join(os.getcwd(), "insightflow.db"),
        os.path.join(os.path.dirname(__file__), "..", "..", "insightflow.db")
    ]
    for src in potential_sources:
        if os.path.exists(src):
            try:
                shutil.copy2(src, "/tmp/insightflow.db")
                break
            except Exception:
                pass

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)
