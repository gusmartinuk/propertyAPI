# Minimal FastAPI (Local = Prod via Docker)

Build and start:
docker compose up -d --build

Logs:
docker compose logs -f --tail=200

Health check:
curl http://localhost/health

Tests:
docker compose run --rm api pytest

Lint/format:
docker compose run --rm api ruff check .
docker compose run --rm api ruff format .
