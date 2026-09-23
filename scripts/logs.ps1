$ErrorActionPreference = "Stop"
$Script:Root = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $Root "docker\docker-compose.yml"
$DevCompose = Join-Path $Root "docker\docker-compose.dev.yml"
$ProdCompose = Join-Path $Root "docker-compose.prod.yml"
$Service = if ($Args[0]) { $Args[0] } else { "" }
$Mode = if ($Args[1]) { $Args[1] } else { "dev" }

if ($Mode -ne "prod") {
    $Override = $DevCompose
} else {
    $Override = $ProdCompose
}

Write-Host "[Docker] Showing logs (tail 200)..." -ForegroundColor Cyan
if ($Service) {
    docker compose -f $ComposeFile -f $Override logs --tail 200 $Service
} else {
    docker compose -f $ComposeFile -f $Override logs --tail 200
}
