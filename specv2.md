STAGE 2 SPEC (Codex) — Minimal Working Skeleton (Local = Prod via Docker)
Objective

Create a minimal FastAPI service that runs production-style locally using Docker Compose:

Reverse proxy: Caddy on http://localhost (port 80)

API: Gunicorn + UvicornWorker (no uvicorn --reload)

DB: PostgreSQL 16 (container + volume)

Tests: pytest inside container

Lint/format: ruff inside container

Must pass: docker compose up -d --build and curl http://localhost/health returns {"status":"ok"}

Constraints

Do not use local .venv at all.

Run everything via Docker.

No secrets committed. Use .env locally and commit .env.example.

Files to create (exact paths)

Create these files with minimal working content:

docker-compose.yml

Caddyfile

Dockerfile

requirements.txt

app/main.py

tests/test_health.py

.env.example

.gitignore

README.md

agent.md (use the git discipline rules already provided in stage 1; if missing, create it)

Implementation details
1) docker-compose.yml

Services:

db:

image: postgres:16

env: POSTGRES_DB=app, POSTGRES_USER=app, POSTGRES_PASSWORD=app_password

volume: pgdata:/var/lib/postgresql/data

healthcheck using pg_isready

expose port 5432:5432 (keep it open for local dev)

api:

build from Dockerfile

env_file: .env

depends_on db with condition service_healthy

internal port: 8000 (do NOT publish to host; only caddy should expose)

caddy:

image: caddy:2

ports: 80:80

mount ./Caddyfile:/etc/caddy/Caddyfile:ro

depends_on: api

2) Caddyfile

Listen on :80

Reverse proxy everything to api:8000

Minimal logging is OK.

3) Dockerfile

Base: python:3.12-slim

Copy requirements.txt then install

Copy project

Run command MUST be gunicorn:

gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000 app.main:app

No reload, no dev-only command.

4) requirements.txt

Minimal deps:

fastapi

gunicorn

uvicorn[standard]

psycopg[binary]

sqlalchemy>=2

alembic

pydantic-settings

pytest

pytest-asyncio

httpx

ruff

5) app/main.py

Create FastAPI app

Routes:

GET / returns plain text e.g. "ok"

GET /health returns JSON { "status": "ok" }

No DB usage yet (DB will be used in later stages)

Keep code tiny.

6) tests/test_health.py

Use fastapi.testclient OR httpx + ASGI transport.

Tests:

/health returns status 200 and JSON {"status": "ok"}

/ returns 200

7) .env.example

Include:

DATABASE_URL=postgresql+psycopg://app:app_password@db:5432/app

ENV=local

LOG_LEVEL=info
Codex must also create a local .env from .env.example BUT must not commit .env.

8) .gitignore

Must include:

.env

__pycache__/

.pytest_cache/

.ruff_cache/

.idea/

.vscode/ (optional)

*.pyc

9) README.md

Include only essential commands:

build/up

logs

curl health

tests

lint/format

Git workflow (mandatory)

Initialize git repo if missing.

Create branch: feat/bootstrap-skeleton

Commit after each logical step with Conventional Commits, e.g.:

chore: bootstrap docker compose with caddy api db

feat: add minimal fastapi app with health endpoint

test: add health endpoint tests

chore: add ruff and pytest container commands docs

Before final commit:

Run: docker compose up -d --build

Run: docker compose logs --tail=50

Run: curl http://localhost/health

Run: docker compose run --rm api pytest

Run: docker compose run --rm api ruff check .

Run: docker compose run --rm api ruff format . (format may modify; commit if it changes files)

Acceptance criteria

docker compose up -d --build succeeds

curl http://localhost/health returns expected JSON

docker compose run --rm api pytest passes

No .env committed

All requested files exist in correct paths