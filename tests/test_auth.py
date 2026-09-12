"""Category: registration / authentication."""
from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_and_login


def test_register_then_login_succeeds(client: TestClient) -> None:
    token = register_and_login(client, "reader@example.com")
    assert token

    me = client.get("/lists", headers=auth_headers(token))
    assert me.status_code == 200


def test_duplicate_registration_is_rejected(client: TestClient) -> None:
    client.post("/auth/register", json={"email": "dup@example.com", "password": "hunter2pass"})
    resp = client.post("/auth/register", json={"email": "dup@example.com", "password": "otherpass1"})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "duplicate_email"


def test_login_with_wrong_password_is_rejected(client: TestClient) -> None:
    client.post("/auth/register", json={"email": "bob@example.com", "password": "correcthorse1"})
    resp = client.post("/auth/login", data={"username": "bob@example.com", "password": "wrongpass1"})
    assert resp.status_code == 401


def test_password_hash_never_appears_in_responses(client: TestClient) -> None:
    resp = client.post(
        "/auth/register", json={"email": "carol@example.com", "password": "hunter2pass"}
    )
    assert "password" not in resp.text
    assert "password_hash" not in resp.text


def test_unauthenticated_access_to_protected_route_is_rejected(client: TestClient) -> None:
    resp = client.get("/lists")
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"
