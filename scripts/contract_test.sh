#!/usr/bin/env bash
set -euo pipefail

max_attempts=30
attempt=1

while [ "$attempt" -le "$max_attempts" ]; do
  if python - <<'PY'
import sys
import requests

try:
    response = requests.get("http://api:8000/health", timeout=2)
    if response.status_code == 200:
        sys.exit(0)
except Exception:
    pass
sys.exit(1)
PY
  then
    break
  fi
  sleep 1
  attempt=$((attempt + 1))
done

if [ "$attempt" -gt "$max_attempts" ]; then
  echo "API not ready after ${max_attempts} attempts." >&2
  exit 1
fi

export HYPOTHESIS_SEED=1

schemathesis run \
  --base-url http://api:8000 \
  --checks all \
  --max-examples 50 \
  --workers 2 \
  --request-timeout 10 \
  --report-junit /reports/junit.xml \
  http://api:8000/openapi.json
