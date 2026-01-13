#!/usr/bin/env pwsh
$maxAttempts = 30

for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
    try {
        $response = Invoke-RestMethod -Uri "http://api:8000/health" -Method Get -TimeoutSec 2
        if ($null -ne $response) {
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

if ($attempt -gt $maxAttempts) {
    Write-Error "API not ready after $maxAttempts attempts."
    exit 1
}

$env:HYPOTHESIS_SEED = "1"

schemathesis run `
    --base-url http://api:8000 `
    --checks all `
    --max-examples 50 `
    --workers 2 `
    --request-timeout 10 `
    --report-junit /reports/junit.xml `
    http://api:8000/openapi.json
