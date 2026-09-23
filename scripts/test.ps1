$ErrorActionPreference = "Stop"
$Script:Root = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $Root "docker\docker-compose.yml"
$DevCompose = Join-Path $Root "docker-compose.override.yml"

Write-Host "[Docker] Running backend tests in container..." -ForegroundColor Cyan
docker compose -f $ComposeFile -f $DevCompose exec -T backend pytest /app/tests -v
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "[Docker] Tests completed." -ForegroundColor Green
