# TESTING.md

Manual test cases run against the real stack (`docker compose up --build`, fresh volume),
via `curl`. Automated coverage of the same categories lives in `tests/` (`pytest -v`, 18
tests, in-memory SQLite — see DESIGN.md for why SQLite there and Postgres here).

All requests below assume `BASE=http://localhost:8000` and a bearer token obtained via
`/auth/login` unless noted.

## Normal flows

### Register

```
POST /auth/register
{"email": "alice@example.com", "password": "hunter2pass"}
```
```
201
{"id":1,"email":"alice@example.com","created_at":"2026-09-12T05:15:14.342028"}
```

### Login

```
POST /auth/login   (form: username=alice@example.com&password=hunter2pass)
```
```
200
{"access_token":"eyJhbGciOiJIUzI1NiIs...","token_type":"bearer"}
```

### Create a list

```
POST /lists   (auth: alice)
{"title": "Sci-Fi Novels"}
```
```
201
{"id":1,"owner_id":1,"title":"Sci-Fi Novels","description":null,
 "created_at":"2026-09-12T05:15:26.457722","updated_at":"2026-09-12T05:15:26.457729"}
```

### Add an item

```
POST /lists/1/items   (auth: alice)
{"title": "Dune", "status": "reading"}
```
```
201
{"id":1,"list_id":1,"title":"Dune","status":"reading","description":null,
 "created_at":"2026-09-12T05:15:26.533158","updated_at":"2026-09-12T05:15:26.533164"}
```

### Paginate items

```
GET /lists/1/items?limit=1&offset=0   (auth: alice)
```
```
200
{"items":[{"id":1,"list_id":1,"title":"Dune", ...}],"total":1,"limit":1,"offset":0}
```

### Export lifecycle (create → check → download)

```
POST /lists/1/exports   (auth: alice)
```
```
202
{"id":1,"list_id":1,"status":"pending","error_message":null,
 "created_at":"2026-09-12T05:15:41.161935","completed_at":null}
```

```
GET /exports/1   (auth: alice, ~50ms later)
```
```
200
{"id":1,"list_id":1,"status":"completed","error_message":null,
 "created_at":"2026-09-12T05:15:41.161935","completed_at":"2026-09-12T05:15:41.207746"}
```

```
GET /exports/1/download   (auth: alice)
```
```
200
{
  "list": {"id":1,"title":"Sci-Fi Novels","description":null},
  "items": [{"id":1,"title":"Dune","status":"reading","description":null}],
  "exported_at": "2026-09-12T05:15:41.207299+00:00"
}
```
The API returned `202` immediately on job creation — it did not wait for the file to be
written; the status only flipped to `completed` on a subsequent poll.

## Robustness cases (Section 3.3)

### 1. Unauthenticated access

```
GET /lists   (no Authorization header)
```
```
401
{"error":{"code":"unauthorized","message":"Missing or malformed Authorization header."}}
```

### 2. Forbidden access (User B on User A's list/item)

Setup: Alice owns list `1` ("Sci-Fi Novels"); Bob is a second registered user.

```
GET /lists/1     (auth: bob)        -> 404 {"error":{"code":"not_found","message":"List not found."}}
PATCH /lists/1   (auth: bob)        -> 404 {"error":{"code":"not_found","message":"List not found."}}
POST /lists/1/items (auth: bob)     -> 404 {"error":{"code":"not_found","message":"List not found."}}
```
Bob's requests are rejected identically to a genuinely nonexistent list id — see DESIGN.md
§Authorization for why 404 (not 403) is used here. Alice's list is confirmed unmodified by a
follow-up `GET /lists/1` as alice, which still returns the original title.

### 3. Forbidden export access (User B on User A's export job)

```
GET /exports/1            (auth: bob) -> 404 {"error":{"code":"not_found","message":"Export job not found."}}
GET /exports/1/download   (auth: bob) -> 404 {"error":{"code":"not_found","message":"Export job not found."}}
```

### 4. Invalid input

Missing required field:
```
POST /lists   (auth: alice)   {}
```
```
422
{"error":{"code":"validation_error","message":"Request data failed validation."},
 "details":[{"type":"missing","loc":["body","title"],"msg":"Field required","input":{}}]}
```

Value violating a business rule (empty title):
```
POST /lists   (auth: alice)   {"title": ""}
```
```
422
{"error":{"code":"validation_error","message":"Request data failed validation."},
 "details":[{"type":"string_too_short","loc":["body","title"],
             "msg":"String should have at least 1 character","input":"","ctx":{"min_length":1}}]}
```

Invalid enum value:
```
POST /lists/1/items   (auth: alice)   {"title": "Bad Book", "status": "nope"}
```
```
422
{"error":{"code":"validation_error","message":"Request data failed validation."},
 "details":[{"type":"enum","loc":["body","status"],
             "msg":"Input should be 'to_read', 'reading' or 'finished'",
             "input":"nope","ctx":{"expected":"'to_read', 'reading' or 'finished'"}}]}
```

### 5. Resource not found

```
GET /lists/999999   (auth: alice, an id that was never issued)
```
```
404
{"error":{"code":"not_found","message":"List not found."}}
```

### 6. Conflict

Duplicate registration:
```
POST /auth/register   {"email": "alice@example.com", "password": "hunter2pass"}   (already registered)
```
```
409
{"error":{"code":"duplicate_email","message":"A user with this email already exists."}}
```

State-constraint conflict (downloading a not-yet-completed export — the code path exists at
`app/api/exports.py::download_export`, returning `409 {"code": "export_not_ready"}` whenever
`job.status != completed`; not independently timed here since the in-process worker finishes
single-item exports in low single-digit milliseconds, faster than a manual `curl` round-trip
can race against).

## Automated test summary

```
$ pytest -v
tests/test_auth.py::test_register_then_login_succeeds PASSED
tests/test_auth.py::test_duplicate_registration_is_rejected PASSED
tests/test_auth.py::test_login_with_wrong_password_is_rejected PASSED
tests/test_auth.py::test_password_hash_never_appears_in_responses PASSED
tests/test_auth.py::test_unauthenticated_access_to_protected_route_is_rejected PASSED
tests/test_authorization.py::test_user_b_cannot_read_user_a_list PASSED
tests/test_authorization.py::test_user_b_cannot_update_or_delete_user_a_list PASSED
tests/test_authorization.py::test_user_b_cannot_add_item_to_user_a_list PASSED
tests/test_authorization.py::test_lists_are_scoped_to_the_requesting_user PASSED
tests/test_validation.py::test_missing_required_field_returns_422 PASSED
tests/test_validation.py::test_password_too_short_is_rejected PASSED
tests/test_validation.py::test_invalid_item_status_value_is_rejected PASSED
tests/test_validation.py::test_empty_list_title_is_rejected PASSED
tests/test_validation.py::test_operation_on_nonexistent_list_returns_404 PASSED
tests/test_export.py::test_export_job_is_created_and_completes PASSED
tests/test_export.py::test_completed_export_can_be_downloaded_and_contains_the_list PASSED
tests/test_export.py::test_export_of_nonexistent_list_returns_404 PASSED
tests/test_export.py::test_user_b_cannot_inspect_or_download_user_a_export PASSED

18 passed
```
