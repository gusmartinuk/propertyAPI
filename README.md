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

Contract Testing (Schemathesis)

Start stack:
docker compose up -d --build

Run contract tests (JUnit report to reports/junit.xml):
docker compose run --rm api bash /app/scripts/contract_test.sh

Windows (PowerShell):
docker compose run --rm api pwsh /app/scripts/contract_test.ps1

Smoke against Caddy (optional):
docker compose run --rm api schemathesis run --base-url http://caddy --checks all --max-examples 20 --workers 2 --request-timeout 10 --report-junit /reports/junit-caddy.xml http://caddy/openapi.json

Troubleshooting:
- If API is not ready, the script retries health up to 30 seconds.
