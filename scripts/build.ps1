$ErrorActionPreference = "Stop"
$Script:Root = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $Root "docker\docker-compose.yml"
$DevCompose = Join-Path $Root "docker\docker-compose.dev.yml"
$ProdCompose = Join-Path $Root "docker-compose.prod.yml"
$Mode = if ($Args[0] -eq "prod") { "production" } else { "development" }

function Write-Info($msg) { Write-Host "[Docker] $msg" -ForegroundColor Cyan }

Write-Info "Building all Docker services ($Mode)..."
if ($Mode -eq "development") {
    $env:DOCKER_BUILDKIT = "1"
    docker compose -f $ComposeFile -f $DevCompose build --no-cache
} else {
    if (Test-Path $ProdCompose) {
        docker compose -f $ComposeFile -f $ProdCompose build --no-cache
    } else {
        docker compose -f $ComposeFile build --no-cache
    }
}
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Info "Build completed successfully."
