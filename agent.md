# Agent Rules (Local Prod-like Docker, Git Discipline)

## Goal
We run everything locally exactly like production using Docker Compose.
No local venv. No local python execution outside containers.

## Commands
- Start: docker compose up -d --build
- Stop: docker compose down
- Logs: docker compose logs -f --tail=200
- Tests: docker compose run --rm api pytest
- Lint: docker compose run --rm api ruff check .
- Format: docker compose run --rm api ruff format .
- Migrations: docker compose run --rm api alembic upgrade head

## Branching
- Work on branch: feat/<short-topic> or chore/<short-topic> or fix/<short-topic>
- Merge to main only when tests and lint pass.

## Commit policy (mandatory)
- Make small changes per commit.
- After each meaningful change:
  1) run tests (or at least relevant tests)
  2) run ruff check
  3) commit with a clear message

## Commit message format (Conventional Commits)
- feat: add health endpoint
- fix: handle db connection errors
- test: add tests for health endpoint
- chore: update docker compose config
- docs: update README

## Do not do
- Do not change multiple unrelated areas in one commit.
- Do not commit secrets (.env, passwords, tokens).
- Do not bypass Docker by running python locally.

## Files that must exist
- docker-compose.yml includes: api, db, caddy
- Caddyfile proxies / to api:8000
- Dockerfile runs gunicorn with uvicorn worker
- requirements.txt includes fastapi, gunicorn, uvicorn, sqlalchemy, alembic, psycopg, pytest, ruff

## Definition of Done
- docker compose up works
- http://localhost/health returns status ok
- tests pass from container
- ruff passes from container
