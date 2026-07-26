# 1) Codex Environment Setup Spec (Local = Production-like)

## Goal

Set up a local environment that behaves like production as closely as possible, with simple one-command workflows:

- Start services with one command:  
  `docker compose up -d --build`
- Run tests with one command:  
  `docker compose run --rm api pytest`
- Route traffic through Caddy on `http://localhost` to the API
- Run API in production mode using Gunicorn + Uvicorn worker
- Use PostgreSQL in a container with a persistent volume
- Manage DB migrations with Alembic inside containers

---

## Repository Structure

```text
myapi/
  app/
    main.py
    settings.py
    db.py
    models.py
  tests/
  alembic/
  alembic.ini
  requirements.txt
  Dockerfile
  docker-compose.yml
  Caddyfile
  .env.example
  .gitignore
  agent.md
```

---

## Docker Compose (Local, Production-like)

### Services

- **db**  
  - Image: `postgres:16`  
  - Persistent volume enabled  
  - Healthcheck configured

- **api**  
  - Built from local `Dockerfile`  
  - Runs on port `8000` via Gunicorn

- **caddy**  
  - Listens on port `80`  
  - Reverse proxies traffic to `api:8000`

### Ports

- `Host 80 -> caddy:80`
- `Host 5432 -> db:5432` *(optional; keep open only if external DB access is needed)*

---

## Environment Variables

Use a local `.env` file (do **not** commit this file):

```env
DATABASE_URL=postgresql+psycopg://app:app_password@db:5432/app
ENV=local
LOG_LEVEL=info
```

---

## Run Commands

### Start services

```bash
docker compose up -d --build
```

### View logs

```bash
docker compose logs -f --tail=200
```

### Run tests

```bash
docker compose run --rm api pytest
```

### Lint / format

```bash
docker compose run --rm api ruff check .
docker compose run --rm api ruff format .
```

### Run migrations

```bash
docker compose run --rm api alembic upgrade head
```

### Create initial migration (first setup)

```bash
docker compose run --rm api alembic revision --autogenerate -m "init"
```

---

## Minimum Endpoints

- `GET /health` -> `{ "status": "ok" }`
- `GET /` -> simple `"service up"` response text

---

## VS Code Setup

- Open the **project root** as the workspace
- In VS Code terminal, run commands only through `docker compose ...`
- Python extension is optional (useful for linting), but all tooling should run via Docker
