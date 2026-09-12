"""Category: cross-user authorization isolation."""
from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_and_login


def _make_list_for(client: TestClient, token: str, title: str = "Sci-Fi Novels") -> int:
    resp = client.post("/lists", json={"title": title}, headers=auth_headers(token))
    assert resp.status_code == 201
    return resp.json()["id"]


def test_user_b_cannot_read_user_a_list(client: TestClient) -> None:
    token_a = register_and_login(client, "alice@example.com")
    token_b = register_and_login(client, "brenda@example.com")
    list_id = _make_list_for(client, token_a)

    resp = client.get(f"/lists/{list_id}", headers=auth_headers(token_b))
    assert resp.status_code == 404  # existence of another user's resource is never confirmed


def test_user_b_cannot_update_or_delete_user_a_list(client: TestClient) -> None:
    token_a = register_and_login(client, "alice2@example.com")
    token_b = register_and_login(client, "brenda2@example.com")
    list_id = _make_list_for(client, token_a)

    update_resp = client.patch(
        f"/lists/{list_id}", json={"title": "hijacked"}, headers=auth_headers(token_b)
    )
    assert update_resp.status_code == 404

    delete_resp = client.delete(f"/lists/{list_id}", headers=auth_headers(token_b))
    assert delete_resp.status_code == 404

    # untouched from A's point of view
    still_there = client.get(f"/lists/{list_id}", headers=auth_headers(token_a))
    assert still_there.status_code == 200
    assert still_there.json()["title"] == "Sci-Fi Novels"


def test_user_b_cannot_add_item_to_user_a_list(client: TestClient) -> None:
    token_a = register_and_login(client, "alice3@example.com")
    token_b = register_and_login(client, "brenda3@example.com")
    list_id = _make_list_for(client, token_a)

    resp = client.post(
        f"/lists/{list_id}/items",
        json={"title": "Dune", "status": "to_read"},
        headers=auth_headers(token_b),
    )
    assert resp.status_code == 404

    items = client.get(f"/lists/{list_id}/items", headers=auth_headers(token_a))
    assert items.json()["total"] == 0


def test_lists_are_scoped_to_the_requesting_user(client: TestClient) -> None:
    token_a = register_and_login(client, "alice4@example.com")
    token_b = register_and_login(client, "brenda4@example.com")
    _make_list_for(client, token_a, "A's shelf")
    _make_list_for(client, token_b, "B's shelf")

    a_lists = client.get("/lists", headers=auth_headers(token_a)).json()
    assert a_lists["total"] == 1
    assert a_lists["items"][0]["title"] == "A's shelf"
