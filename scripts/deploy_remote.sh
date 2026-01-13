#!/usr/bin/env bash
set -e

cd /opt/ppd-api

git fetch --all
git reset --hard origin/main

docker compose up -d --build

if [ -f alembic.ini ]; then
  docker compose exec -T api alembic upgrade head
fi

curl -fsS http://localhost/health > /dev/null
