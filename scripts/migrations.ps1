$ErrorActionPreference = "Stop"
$Script:Root = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $Root "docker\docker-compose.yml"
$DevCompose = Join-Path $Root "docker\docker-compose.dev.yml"
$ProdCompose = Join-Path $Root "docker-compose.prod.yml"
$Mode = if ($Args[0] -eq "prod") { "production" } else { "development" }

if ($Mode -eq "development") {
    docker compose -f $ComposeFile -f $DevCompose exec -T backend python -m app.database.migrate
} else {
    docker compose -f $ComposeFile -f $ProdCompose exec -T backend python -m app.database.migrate
}

if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "[Docker] Migrations applied successfully." -ForegroundColor Green
