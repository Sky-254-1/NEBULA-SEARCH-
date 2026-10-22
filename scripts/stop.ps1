$ErrorActionPreference = "Stop"
$Script:Root = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $Root "docker\docker-compose.yml"
$DevCompose = Join-Path $Root "docker\docker-compose.dev.yml"
$ProdCompose = Join-Path $Root "docker-compose.prod.yml"

Write-Host "[Docker] Stopping all services..." -ForegroundColor Cyan
docker compose -f $ComposeFile -f $DevCompose down 2>$null
if ($LASTEXITCODE -ne 0) {
    docker compose -f $ComposeFile down 2>$null
}
if (Test-Path $ProdCompose) {
    docker compose -f $ComposeFile -f $ProdCompose down 2>$null
}
Write-Host "[Docker] Services stopped." -ForegroundColor Green
