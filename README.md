# Minimal FastAPI (Local = Prod via Docker)

[![CI](https://github.com/gusmartinuk/propertyAPI/actions/workflows/deploy.yml/badge.svg)](https://github.com/gusmartinuk/propertyAPI/actions/workflows/deploy.yml)

Data Source: https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads

Build and start:
docker compose up -d --build

Logs:
docker compose logs -f --tail=200

Health check:
curl http://localhost/health

Auth (non-RapidAPI):
- Use header `X-API-Key`
- Keys are loaded from `config/api_keys.txt` (hot-reload)

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
powershell -File .\\scripts\\contract_test.ps1

Fast contract run (JUnit report to reports/junit-fast.xml):
tests.bat fast

Smoke against Caddy (optional):
docker compose run --rm api schemathesis run --url http://caddy --checks all --max-examples 20 --workers 2 --request-timeout 10 --report-junit-path /reports/junit-caddy.xml http://caddy/openapi.json

Troubleshooting:
- If API is not ready, the script retries health up to 30 seconds.
