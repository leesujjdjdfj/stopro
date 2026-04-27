from __future__ import annotations

import os

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings


settings = get_settings()
database_url = settings.database_url
if os.getenv("VERCEL") and database_url == "sqlite:///./stopro.db":
    database_url = "sqlite:////tmp/stopro.db"

connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, connect_args=connect_args)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
