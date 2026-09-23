$ErrorActionPreference = "Stop"
$Script:Root = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $Root "docker\docker-compose.yml"
$DevCompose = Join-Path $Root "docker\docker-compose.dev.yml"
$ProdCompose = Join-Path $Root "docker-compose.prod.yml"
$Mode = if ($Args[0] -eq "prod") { "production" } else { "development" }

$Confirm = Read-Host "This will remove all volumes and recreate containers. Continue? (y/N)"
if ($Confirm -ne "y") { Write-Host "Aborted."; exit 0 }

Write-Host "[Docker] Resetting environment..." -ForegroundColor Cyan
if ($Mode -eq "development") {
    docker compose -f $ComposeFile -f $DevCompose down -v
} else {
    docker compose -f $ComposeFile -f $ProdCompose down -v
}
docker system prune -f
Write-Host "[Docker] Reset complete. Run .\scripts\start.ps1 to restart." -ForegroundColor Green
