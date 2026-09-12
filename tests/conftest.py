import os
import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.config import settings
from app.main import app
import app.workers.export as export_worker

# In-memory SQLite keeps the test suite hermetic and fast; it does not need a
# running Postgres. See DESIGN.md for why this is an acceptable trade-off
# here (the ORM layer, not raw SQL, is what's under test).
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db
# The background export worker opens its own session (see workers/export.py's
# docstring for why) rather than reusing the request-scoped one, so it needs
# its own override to land in the same in-memory SQLite database.
export_worker.SessionLocal = TestingSessionLocal


@pytest.fixture(autouse=True)
def _fresh_database(tmp_path) -> Generator[None, None, None]:
    settings.export_dir = str(tmp_path)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


def register_and_login(client: TestClient, email: str, password: str = "hunter2pass") -> str:
    resp = client.post("/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text
    resp = client.post("/auth/login", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
