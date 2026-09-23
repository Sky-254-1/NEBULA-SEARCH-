# Nebula Search - Production Deployment Script
# This script automates the deployment process using Docker Compose

param(
    [switch]$SkipTests = $false,
    [switch]$SkipBuild = $false,
    [string]$ComposeFile = "..\docker-compose.prod.yml"
)

$ErrorActionPreference = "Stop"
$rootDir = ".."

Write-Host "`n=== Nebula Search - Production Deployment ===`n" -ForegroundColor Cyan

# Verify Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Error "Docker is not running. Please start Docker Desktop and try again."
    exit 1
}

# Verify .env.production exists
$envFile = "$rootDir\.env.production"
if (-not (Test-Path $envFile)) {
    Write-Warning ".env.production not found. Creating from .env.example..."
    Copy-Item "$rootDir\.env.example" $envFile
    Write-Host "⚠️  Please edit .env.production and fill in your secrets before continuing!" -ForegroundColor Red
    Write-Host "   Required: JWT_SECRET, POSTGRES_PASSWORD, MINIO_ROOT_PASSWORD, GRAFANA_ADMIN_PASSWORD`n" -ForegroundColor Yellow
    $continue = Read-Host "Have you updated .env.production? (y/N)"
    if ($continue -ne "y") {
        Write-Host "Deployment cancelled. Please update .env.production and run this script again." -ForegroundColor Yellow
        exit 0
    }
}

# Step 1: Generate favicon.ico if missing
$faviconPath = "$rootDir\backend\static\favicon.ico"
if (-not (Test-Path $faviconPath)) {
    Write-Host "`n[1/5] Generating favicon.ico..." -ForegroundColor Cyan
    Push-Location "$rootDir\scripts"
    try {
        .\generate-favicon.ps1
    } catch {
        Write-Warning "Failed to generate favicon.ico: $_"
        Write-Host "You can manually convert frontend/public/favicon.svg to ICO later." -ForegroundColor Yellow
    }
    Pop-Location
} else {
    Write-Host "`n[1/5] favicon.ico already exists, skipping." -ForegroundColor Green
}

# Step 2: Pull latest images
Write-Host "`n[2/5] Pulling latest base images..." -ForegroundColor Cyan
Push-Location $rootDir
try {
    docker compose -f $ComposeFile pull
} catch {
    Write-Warning "Failed to pull some images: $_"
}
Pop-Location

# Step 3: Build application images
if (-not $SkipBuild) {
    Write-Host "`n[3/5] Building application images..." -ForegroundColor Cyan
    Push-Location $rootDir
    try {
        docker compose -f $ComposeFile build --no-cache
    } catch {
        Write-Error "Build failed: $_"
        Pop-Location
        exit 1
    }
    Pop-Location
} else {
    Write-Host "`n[3/5] Skipping build (--SkipBuild specified)" -ForegroundColor Yellow
}

# Step 4: Start services
Write-Host "`n[4/5] Starting services..." -ForegroundColor Cyan
Push-Location $rootDir
try {
    docker compose -f $ComposeFile up -d
} catch {
    Write-Error "Failed to start services: $_"
    Pop-Location
    exit 1
}
Pop-Location

# Step 5: Wait for services to be healthy
Write-Host "`n[5/5] Waiting for services to be healthy..." -ForegroundColor Cyan
Write-Host "This may take 30-60 seconds...`n" -ForegroundColor Yellow

$maxWait = 120
$waited = 0
$interval = 5

while ($waited -lt $maxWait) {
    Start-Sleep -Seconds $interval
    $waited += $interval
    
    $backendHealth = docker compose -f $ComposeFile ps backend --format "{{.Health}}" 2>$null
    $frontendHealth = docker compose -f $ComposeFile ps frontend --format "{{.Health}}" 2>$null
    $postgresHealth = docker compose -f $ComposeFile ps postgres --format "{{.Health}}" 2>$null
    $redisHealth = docker compose -f $ComposeFile ps redis --format "{{.Health}}" 2>$null
    
    Write-Host "  Backend: $backendHealth | Frontend: $frontendHealth | PostgreSQL: $postgresHealth | Redis: $redisHealth" -ForegroundColor Gray
    
    if ($backendHealth -eq "healthy" -and $frontendHealth -eq "healthy") {
        Write-Host "`n✅ All services are healthy!" -ForegroundColor Green
        break
    }
}

if ($waited -ge $maxWait) {
    Write-Host "`n⚠️  Timeout waiting for services. Check logs with:" -ForegroundColor Yellow
    Write-Host "   docker compose -f $ComposeFile logs`n" -ForegroundColor White
}

# Run database migrations
Write-Host "`nRunning database migrations..." -ForegroundColor Cyan
try {
    docker compose -f $ComposeFile exec -T backend alembic upgrade head
    Write-Host "✅ Migrations complete" -ForegroundColor Green
} catch {
    Write-Warning "Migration failed (this is normal on first run if database is not initialized): $_"
}

# Display service URLs
Write-Host "`n=== Deployment Complete ===`n" -ForegroundColor Green
Write-Host "Service URLs:" -ForegroundColor Cyan
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  MinIO:     http://localhost:9000" -ForegroundColor White
Write-Host "  Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "  Grafana:   http://localhost:3001`n" -ForegroundColor White

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Verify health: .\verify-deployment.ps1" -ForegroundColor White
Write-Host "  2. View logs: docker compose -f $ComposeFile logs -f" -ForegroundColor White
Write-Host "  3. Stop services: docker compose -f $ComposeFile down`n" -ForegroundColor White