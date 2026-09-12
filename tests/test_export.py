"""Category: export lifecycle (plus forbidden-export-access, another required
robustness case from Section 3.3)."""
from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_and_login


def _make_list_with_item(client: TestClient, token: str) -> int:
    list_resp = client.post(
        "/lists", json={"title": "Sci-Fi Novels"}, headers=auth_headers(token)
    )
    list_id = list_resp.json()["id"]
    client.post(
        f"/lists/{list_id}/items",
        json={"title": "Dune", "status": "reading"},
        headers=auth_headers(token),
    )
    return list_id


def test_export_job_is_created_and_completes(client: TestClient) -> None:
    token = register_and_login(client, "gina@example.com")
    list_id = _make_list_with_item(client, token)

    create_resp = client.post(f"/lists/{list_id}/exports", headers=auth_headers(token))
    assert create_resp.status_code == 202
    job = create_resp.json()
    assert job["status"] in ("pending", "completed")
    job_id = job["id"]

    # TestClient runs BackgroundTasks inline, so by the time we ask again the
    # in-process worker has already finished.
    status_resp = client.get(f"/exports/{job_id}", headers=auth_headers(token))
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "completed"


def test_completed_export_can_be_downloaded_and_contains_the_list(client: TestClient) -> None:
    token = register_and_login(client, "hank@example.com")
    list_id = _make_list_with_item(client, token)

    job_id = client.post(f"/lists/{list_id}/exports", headers=auth_headers(token)).json()["id"]

    download = client.get(f"/exports/{job_id}/download", headers=auth_headers(token))
    assert download.status_code == 200
    body = download.json()
    assert body["list"]["title"] == "Sci-Fi Novels"
    assert body["items"][0]["title"] == "Dune"


def test_export_of_nonexistent_list_returns_404(client: TestClient) -> None:
    token = register_and_login(client, "ivan@example.com")
    resp = client.post("/lists/999999/exports", headers=auth_headers(token))
    assert resp.status_code == 404


def test_user_b_cannot_inspect_or_download_user_a_export(client: TestClient) -> None:
    token_a = register_and_login(client, "judy@example.com")
    token_b = register_and_login(client, "ken@example.com")
    list_id = _make_list_with_item(client, token_a)
    job_id = client.post(f"/lists/{list_id}/exports", headers=auth_headers(token_a)).json()["id"]

    status_resp = client.get(f"/exports/{job_id}", headers=auth_headers(token_b))
    assert status_resp.status_code == 404

    download_resp = client.get(f"/exports/{job_id}/download", headers=auth_headers(token_b))
    assert download_resp.status_code == 404
