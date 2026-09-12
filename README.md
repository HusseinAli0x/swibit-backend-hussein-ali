# Swibit Backend Task — Personal Catalog API

A backend service where each user owns **lists**, and each list contains **items**.

**Domain flavor: reading tracker.** A list is a *shelf* (e.g. "Sci-Fi Novels"), an item is a
*book* on that shelf, with a reading-progress `status`: `to_read` / `reading` / `finished`.
The resources are still called `list`/`item` everywhere in the code, database schema, and API
routes — the reading-tracker framing only shows up in field values and examples.

Built with FastAPI + PostgreSQL + SQLAlchemy/Alembic, JWT auth, and an in-process background
export worker. See [DESIGN.md](DESIGN.md) for architecture and trade-offs, and
[TESTING.md](TESTING.md) for manual test cases (including all required robustness cases).

## Quick start

```bash
cp .env.example .env        # defaults work as-is for local Docker use
docker compose up --build
```

That single command builds the image, starts Postgres, waits for it to be healthy, runs
Alembic migrations, and starts the API — nothing else is required. The API is then available
at `http://localhost:8000`, interactive docs at `http://localhost:8000/docs`.

To stop: `docker compose down` (add `-v` to also drop the Postgres volume).

### Running tests

Tests run against an in-memory SQLite database (no Postgres/Docker required) — see
[DESIGN.md](DESIGN.md#testing-strategy) for why.

```bash
python3 -m venv .venv
source .venv/bin/activate   # or `.venv/bin/pip install ...` directly
pip install -r requirements.txt
pytest -v
```

## Environment variables

All variables are listed with safe placeholder defaults in `.env.example`.

| Variable | Used by | Purpose |
|---|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `db` container | Postgres bootstrap credentials |
| `DATABASE_URL` | API | SQLAlchemy connection string (must match the `POSTGRES_*` values) |
| `SECRET_KEY` | API | JWT signing secret — generate a real one with `openssl rand -hex 32` for anything beyond local dev |
| `ALGORITHM` | API | JWT signing algorithm (`HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | API | Access token lifetime |
| `EXPORT_DIR` | API | Where the background worker writes export JSON files (inside the container) |

## API overview

All request/response bodies are JSON except `/auth/login`, which uses the standard OAuth2
password-flow form encoding (`username`/`password`) so Swagger's "Authorize" button works
out of the box against it. `username` is the user's email.

Protected endpoints require `Authorization: Bearer <access_token>`.

### Auth

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create an account (`email`, `password`) |
| POST | `/auth/login` | Exchange credentials for a JWT access token |

```bash
curl -X POST localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email": "alice@example.com", "password": "hunter2pass"}'

curl -X POST localhost:8000/auth/login \
  -d 'username=alice@example.com&password=hunter2pass'
# -> {"access_token": "...", "token_type": "bearer"}
```

### Lists

| Method | Path | Description |
|---|---|---|
| POST | `/lists` | Create a list |
| GET | `/lists?limit=&offset=` | Paginated list of your lists |
| GET | `/lists/{list_id}` | Get one of your lists |
| PATCH | `/lists/{list_id}` | Partial update |
| DELETE | `/lists/{list_id}` | Delete (cascades to its items) |

```bash
curl -X POST localhost:8000/lists \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"title": "Sci-Fi Novels"}'
```

### Items (nested under a list)

| Method | Path | Description |
|---|---|---|
| POST | `/lists/{list_id}/items` | Add an item to your list |
| GET | `/lists/{list_id}/items?limit=&offset=` | Paginated list of items in your list |
| GET | `/lists/{list_id}/items/{item_id}` | Get one item |
| PATCH | `/lists/{list_id}/items/{item_id}` | Partial update (title/status/description) |
| DELETE | `/lists/{list_id}/items/{item_id}` | Delete |

```bash
curl -X POST localhost:8000/lists/1/items \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"title": "Dune", "status": "reading"}'
```

`status` is one of `to_read`, `reading`, `finished`.

### Export (background job)

| Method | Path | Description |
|---|---|---|
| POST | `/lists/{list_id}/exports` | Kick off a background export of that list to JSON. Returns immediately (`202`) with a `pending` job. |
| GET | `/exports?limit=&offset=` | Paginated list of your export jobs |
| GET | `/exports/{job_id}` | Check job status: `pending` / `completed` / `failed` |
| GET | `/exports/{job_id}/download` | Download the finished JSON file (`409` if not yet completed) |

```bash
JOB_ID=$(curl -s -X POST localhost:8000/lists/1/exports -H "Authorization: Bearer $TOKEN" | jq .id)
curl localhost:8000/exports/$JOB_ID -H "Authorization: Bearer $TOKEN"
curl localhost:8000/exports/$JOB_ID/download -H "Authorization: Bearer $TOKEN"
```

### Errors

Every error response has the shape:

```json
{"error": {"code": "not_found", "message": "List not found."}}
```

(422 validation errors additionally include a `details` array with per-field errors.) See
[TESTING.md](TESTING.md) for the exact status code used for each failure case.

## Known limitations

- The export worker runs in-process via FastAPI `BackgroundTasks`: a job in progress is lost
  if the API process restarts (it stays `pending` forever rather than resuming). Acceptable
  for this assessment's scope; see DESIGN.md for the production alternative.
- Export files are stored on the API container's local filesystem, not object storage —
  fine for a single-instance deployment, not for horizontal scaling.
- No rate limiting, refresh tokens, or password reset flow — out of scope for the assignment.
- SQLite is used for the automated test suite instead of Postgres, so Postgres-only behavior
  (native enum constraints) isn't exercised by `pytest` itself, only by the manual tests in
  TESTING.md against the real Docker stack.

## Bonus

- **CI/CD**: `.github/workflows/ci.yml` runs the pytest suite on every push and pull request.

## AI Tools Used

Claude Code (Anthropic) was used throughout: scaffolding the FastAPI project structure,
writing the models/schemas/routers/tests, debugging a Postgres-native-enum serialization bug
and a passlib/bcrypt5 incompatibility found while running the stack end-to-end in Docker, and
drafting this documentation. All code was reviewed and is understood by the author.
