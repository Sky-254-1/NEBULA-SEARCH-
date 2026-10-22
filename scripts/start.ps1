$ErrorActionPreference = "Stop"
$Script:Root = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $Root "docker\docker-compose.yml"
$DevCompose = Join-Path $Root "docker\docker-compose.dev.yml"
$ProdCompose = Join-Path $Root "docker-compose.prod.yml"
$EnvFile = Join-Path $Root "backend\.env"
$RootEnvFile = Join-Path $Root ".env"
$Mode = if ($Args[0] -eq "prod") { "production" } else { "development" }

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[Docker] Docker is not installed or not in PATH. Exiting." -ForegroundColor Red
    exit 1
}

function Test-EnvFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        Write-Warning "$Path not found. Copying from .env.example..."
        $example = $Path -replace '\.env$', '.env.example'
        if (-not (Test-Path $example)) {
            Write-Host "$example not found either. Exiting." -ForegroundColor Red
            exit 1
        }
        Copy-Item $example $Path
    }
    $content = Get-Content $Path -Raw
    if ($content -match 'change-this|your-|secret|CHANGE|TODO') {
        Write-Host "WARNING: $Path contains placeholder values. Please update it before proceeding." -ForegroundColor Yellow
    }
}

Test-EnvFile -Path $RootEnvFile
Test-EnvFile -Path $EnvFile

if ($Mode -eq "development") {
    Write-Host "[Docker] Starting in DEVELOPMENT mode..." -ForegroundColor Cyan
    docker compose -f $ComposeFile -f $DevCompose up -d --build
} else {
    Write-Host "[Docker] Starting in PRODUCTION mode..." -ForegroundColor Cyan
    if (-not (Test-Path $ProdCompose)) {
        Write-Host "docker-compose.prod.yml not found. Using base compose only." -ForegroundColor Yellow
        docker compose -f $ComposeFile up -d
    } else {
        docker compose -f $ComposeFile -f $ProdCompose up -d
    }
}

if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "[Docker] Services started. Run .\scripts\logs.ps1 to see output." -ForegroundColor Green
Write-Host "[Docker] To run migrations: .\scripts\migrations.ps1" -ForegroundColor Cyan
