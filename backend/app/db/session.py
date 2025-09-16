from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine

from ..config import settings

_database_url = settings.database_url

if _database_url.startswith("sqlite"):
    db_path_str = _database_url.removeprefix("sqlite:///")
    db_path = Path(db_path_str)
    if not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(_database_url, echo=settings.database_echo, future=True)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Session:
    with Session(engine) as session:
        yield session
