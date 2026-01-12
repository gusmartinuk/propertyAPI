1) Codex Ortam Hazırlama Spec (Local = Prod)
Hedef

Tek komutla ayağa kalksın: docker compose up -d --build

Tek komutla test: docker compose run --rm api pytest

Trafik: http://localhost üzerinden Caddy -> API

API prod modu: gunicorn + uvicorn worker

DB: Postgres container, kalıcı volume

Migration: Alembic, container içinde çalıştırılır

Repo yapısı
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

Docker Compose (local prod-like)

Servisler:

db : postgres:16 + volume + healthcheck

api: Dockerfile build, gunicorn ile 8000’de

caddy: 80’den dinler, api:8000’e proxy

Portlar:

Host: 80 -> caddy:80

Host: 5432 -> db:5432 (opsiyonel; dışarıdan bağlanmak istersen açık kalsın)

Ortam değişkenleri

.env (repoya girmez)

DATABASE_URL=postgresql+psycopg://app:app_password@db:5432/app

ENV=local

LOG_LEVEL=info

Çalıştırma komutları

Başlat:

docker compose up -d --build

Log:

docker compose logs -f --tail=200

Test:

docker compose run --rm api pytest

Lint/format:

docker compose run --rm api ruff check .

docker compose run --rm api ruff format .

Migration:

docker compose run --rm api alembic upgrade head

(ilk kurulumda) docker compose run --rm api alembic revision --autogenerate -m "init"

Minimum endpointler

GET /health -> { "status": "ok" }

GET / -> basit “service up” metni

VS Code ayarı

Workspace: proje kökü

Terminal: VS Code içinde sadece docker compose ... çalıştırılacak

Python extension zorunlu değil, sadece lint için istersen (ama tool çalıştırma Docker üzerinden)