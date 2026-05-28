from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _sqlite_path(database_url: str) -> Path | None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    raw_path = database_url.removeprefix(prefix)
    if raw_path in ("", ":memory:"):
        return None
    return Path(raw_path)


def get_engine() -> Engine:
    global _engine, _session_factory
    settings = get_settings()
    database_url = settings.database_url

    if _engine is not None and str(_engine.url) == database_url:
        return _engine

    sqlite_path = _sqlite_path(database_url)
    if sqlite_path is not None:
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)

    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    _engine = create_engine(database_url, connect_args=connect_args)
    _session_factory = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


def init_db() -> None:
    import app.models  # noqa: F401
    from app.migrations import migrate_sqlite_schema

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    migrate_sqlite_schema(engine)


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()
