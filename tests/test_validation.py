"""Category: invalid input / database constraints."""
from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_and_login


def test_missing_required_field_returns_422(client: TestClient) -> None:
    resp = client.post("/auth/register", json={"email": "x@example.com"})  # no password
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "validation_error"


def test_password_too_short_is_rejected(client: TestClient) -> None:
    resp = client.post("/auth/register", json={"email": "y@example.com", "password": "short"})
    assert resp.status_code == 422


def test_invalid_item_status_value_is_rejected(client: TestClient) -> None:
    token = register_and_login(client, "dana@example.com")
    list_resp = client.post("/lists", json={"title": "Fantasy"}, headers=auth_headers(token))
    list_id = list_resp.json()["id"]

    resp = client.post(
        f"/lists/{list_id}/items",
        json={"title": "The Hobbit", "status": "not_a_real_status"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 422


def test_empty_list_title_is_rejected(client: TestClient) -> None:
    token = register_and_login(client, "erin@example.com")
    resp = client.post("/lists", json={"title": ""}, headers=auth_headers(token))
    assert resp.status_code == 422


def test_operation_on_nonexistent_list_returns_404(client: TestClient) -> None:
    token = register_and_login(client, "frank@example.com")
    resp = client.get("/lists/999999", headers=auth_headers(token))
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"
