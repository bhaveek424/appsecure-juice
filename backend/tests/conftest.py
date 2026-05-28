import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
import app.models  # noqa: F401
from app.db import Base, get_db
from app.main import app


@pytest.fixture(autouse=True)
def clear_settings_cache(monkeypatch):
    monkeypatch.setenv(
        "TARGET_APPLICATION_URL", "http://juice-shop:3000"
    )
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client(monkeypatch):
    import app.db as db_module
    from app.zap.client import MockZapClient
    from app.reasoning import factory as reasoning_factory
    from app.zap import factory as zap_factory

    zap_factory.set_zap_client(MockZapClient())
    reasoning_factory.clear_reasoning_client()
    monkeypatch.setattr("app.main.init_db", lambda: None)

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_module._engine = engine
    db_module._session_factory = TestingSession

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    zap_factory.clear_zap_client()
    reasoning_factory.clear_reasoning_client()
    db_module._engine = None
    db_module._session_factory = None
    Base.metadata.drop_all(bind=engine)
