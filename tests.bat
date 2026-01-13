@echo off
set MODE=%1

docker compose up -d --build

if /I "%MODE%"=="fast" (
  powershell -File .\scripts\contract_test_fast.ps1
) else (
  powershell -File .\scripts\contract_test.ps1
)

docker compose run --rm api pytest
docker compose run --rm api ruff check .
