# Stage 2 Specification (Codex): Minimal Working Skeleton (Local = Production via Docker)

## Objective

Create a minimal FastAPI service that runs in a production-like way locally using Docker Compose.

### Runtime topology

- **Reverse proxy:** Caddy on `http://localhost` (port `80`)
- **API:** Gunicorn + `UvicornWorker` (no `uvicorn --reload`)
- **Database:** PostgreSQL 16 (container + persistent volume)
- **Tests:** `pytest` inside the API container
- **Lint/format:** `ruff` inside the API container

### Must pass

- `docker compose up -d --build`
- `curl http://localhost/health` returns:
  - `{"status":"ok"}`

## Constraints

- Do **not** use a local `.venv`.
- Run everything through Docker.
- Do **not** commit secrets.
- Use `.env` locally and commit `.env.example`.

## Files to create (exact paths)

Create the following files with minimal working content:

- `docker-compose.yml`
- `Caddyfile`
- `Dockerfile`
- `requirements.txt`
- `app/main.py`
- `tests/test_health.py`
- `.env.example`
- `.gitignore`
- `README.md`
- `agent.md` (use the Git discipline rules already provided in Stage 1; if missing, create it)

## Implementation details

### 1) `docker-compose.yml`

Define the following services:

#### `db`

- `image: postgres:16`
- Environment variables:
  - `POSTGRES_DB=app`
  - `POSTGRES_USER=app`
  - `POSTGRES_PASSWORD=app_password`
- Volume:
  - `pgdata:/var/lib/postgresql/data`
- Healthcheck:
  - Use `pg_isready`
- Ports:
  - Expose `5432:5432` (keep available for local development)

#### `api`

- Build from `Dockerfile`
- `env_file: .env`
- `depends_on: db` with condition `service_healthy`
- Internal port:
  - `8000`
- Do **not** publish API directly to host (only Caddy should expose externally)

#### `caddy`

- `image: caddy:2`
- Ports:
  - `80:80`
- Mount:
  - `./Caddyfile:/etc/caddy/Caddyfile:ro`
- `depends_on: api`

---

### 2) `Caddyfile`

- Listen on `:80`
- Reverse proxy all traffic to `api:8000`
- Minimal logging is acceptable

---

### 3) `Dockerfile`

- Base image: `python:3.12-slim`
- Copy `requirements.txt`, then install dependencies
- Copy project files
- Runtime command **must** be Gunicorn:

```bash
gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000 app.main:app
```

- No reload mode
- No development-only runtime command

---

### 4) `requirements.txt`

Minimum dependencies:

- `fastapi`
- `gunicorn`
- `uvicorn[standard]`
- `psycopg[binary]`
- `sqlalchemy>=2`
- `alembic`
- `pydantic-settings`
- `pytest`
- `pytest-asyncio`
- `httpx`
- `ruff`

---

### 5) `app/main.py`

- Create a FastAPI app
- Routes:
  - `GET /` returns plain text (e.g. `"ok"`)
  - `GET /health` returns JSON: `{ "status": "ok" }`
- Do not use the database yet (database integration is for later stages)
- Keep implementation intentionally minimal

---

### 6) `tests/test_health.py`

Use `fastapi.testclient` **or** `httpx` with ASGI transport.

Tests required:

- `/health` returns status `200` and JSON `{"status": "ok"}`
- `/` returns status `200`

---

### 7) `.env.example`

Include:

```env
DATABASE_URL=postgresql+psycopg://app:app_password@db:5432/app
ENV=local
LOG_LEVEL=info
```

Codex must also create a local `.env` from `.env.example`, but must **not** commit `.env`.

---

### 8) `.gitignore`

Must include:

- `.env`
- `__pycache__/`
- `.pytest_cache/`
- `.ruff_cache/`
- `.idea/`
- `.vscode/` (optional)
- `*.pyc`

---

### 9) `README.md`

Include only essential commands for:

- build/up
- logs
- health check via `curl`
- tests
- lint/format

## Git workflow (mandatory)

- Initialise Git repository if missing.
- Create branch: `feat/bootstrap-skeleton`
- Commit after each logical step using Conventional Commits, e.g.:
  - `chore: bootstrap docker compose with caddy api db`
  - `feat: add minimal fastapi app with health endpoint`
  - `test: add health endpoint tests`
  - `chore: add ruff and pytest container commands docs`

### Before final commit

Run:

- `docker compose up -d --build`
- `docker compose logs --tail=50`
- `curl http://localhost/health`
- `docker compose run --rm api pytest`
- `docker compose run --rm api ruff check .`
- `docker compose run --rm api ruff format .`
  - Formatting may modify files; commit changes if it does

## Acceptance criteria

- `docker compose up -d --build` succeeds
- `curl http://localhost/health` returns expected JSON
- `docker compose run --rm api pytest` passes
- No `.env` file is committed
- All requested files exist at the correct paths
