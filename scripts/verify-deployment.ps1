# Nebula Search - Deployment Verification Script
# This script verifies that all services are running and healthy

param(
    [string]$ComposeFile = "..\docker-compose.prod.yml",
    [int]$Timeout = 30
)

$ErrorActionPreference = "Stop"
$rootDir = ".."

Write-Host "`n=== Nebula Search - Deployment Verification ===`n" -ForegroundColor Cyan

# Function to test HTTP endpoint
function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Name,
        [int]$ExpectedStatus = 200,
        [int]$TimeoutSeconds = 10
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Head -TimeoutSec $TimeoutSeconds -UseBasicParsing
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Host "  ✅ $Name : $Url" -ForegroundColor Green
            return $true
        } else {
            Write-Host "  ❌ $Name : Expected $ExpectedStatus, got $($response.StatusCode)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "  ❌ $Name : $Url - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Check Docker is running
Write-Host "Checking Docker..." -ForegroundColor Cyan
try {
    docker info | Out-Null
    Write-Host "  ✅ Docker is running`n" -ForegroundColor Green
} catch {
    Write-Error "  ❌ Docker is not running. Please start Docker Desktop.`n"
    exit 1
}

# Check containers are running
Write-Host "Checking containers..." -ForegroundColor Cyan
$containers = @("postgres", "redis", "backend", "frontend", "nginx", "storage")
$allRunning = $true

foreach ($container in $containers) {
    $status = docker compose -f $ComposeFile ps $container --format "{{.State}}" 2>$null
    if ($status -eq "running") {
        Write-Host "  ✅ $container is running" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $container is not running (state: $status)" -ForegroundColor Red
        $allRunning = $false
    }
}

if (-not $allRunning) {
    Write-Host "`n⚠️  Some containers are not running. Check logs with:" -ForegroundColor Yellow
    Write-Host "   docker compose -f $ComposeFile logs`n" -ForegroundColor White
    exit 1
}

# Check container health
Write-Host "`nChecking container health..." -ForegroundColor Cyan
$healthChecks = @("postgres", "redis", "backend", "frontend")
$allHealthy = $true

foreach ($service in $healthChecks) {
    $health = docker compose -f $ComposeFile ps $service --format "{{.Health}}" 2>$null
    if ($health -eq "healthy") {
        Write-Host "  ✅ $service is healthy" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  $service health: $health" -ForegroundColor Yellow
        $allHealthy = $false
    }
}

# Wait for services to be ready
Write-Host "`nWaiting for services to be ready..." -ForegroundColor Cyan
$maxWait = $Timeout
$waited = 0
$interval = 2

while ($waited -lt $maxWait) {
    Start-Sleep -Seconds $interval
    $waited += $interval
    
    try {
        $health = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -UseBasicParsing
        if ($health.StatusCode -eq 200) {
            Write-Host "  ✅ Backend is ready (waited ${waited}s)`n" -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "  ⏳ Waiting for backend... ($waited/$maxWait seconds)" -ForegroundColor Gray
    }
}

if ($waited -ge $maxWait) {
    Write-Host "  ⚠️  Backend did not respond within $maxWait seconds`n" -ForegroundColor Yellow
}

# Test health endpoints
Write-Host "Testing health endpoints..." -ForegroundColor Cyan
$results = @()

$results += Test-Endpoint -Url "http://localhost:8000/health" -Name "Backend Health"
$results += Test-Endpoint -Url "http://localhost:8000/api/v1/health" -Name "API Health"
$results += Test-Endpoint -Url "http://localhost:3000/health.html" -Name "Frontend Health"

# Test API endpoints
Write-Host "`nTesting API endpoints..." -ForegroundColor Cyan
$apiResults = @()

# Test unauthenticated endpoint
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/signup" -Method Post -ContentType "application/json" -Body '{"email":"test@test.com","password":"Test123!"}' -ErrorAction Stop
    if ($response -match "already exists" -or $response -match "created") {
        Write-Host "  ✅ Auth API responding" -ForegroundColor Green
        $apiResults += $true
    }
} catch {
    if ($_.Exception.Response.StatusCode -eq 422) {
        Write-Host "  ✅ Auth API responding (validation error expected)" -ForegroundColor Green
        $apiResults += $true
    } else {
        Write-Host "  ❌ Auth API error: $($_.Exception.Message)" -ForegroundColor Red
        $apiResults += $false
    }
}

# Test search endpoint (should require auth)
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/search/web?q=test" -Method Get -ErrorAction SilentlyContinue
    Write-Host "  ⚠️  Search API: Unexpected success (should require auth)" -ForegroundColor Yellow
    $apiResults += $false
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "  ✅ Search API correctly requires authentication" -ForegroundColor Green
        $apiResults += $true
    } else {
        Write-Host "  ⚠️  Search API error: $($_.Exception.Message)" -ForegroundColor Yellow
        $apiResults += $false
    }
}

# Check MinIO
Write-Host "`nChecking MinIO storage..." -ForegroundColor Cyan
try {
    $minioHealth = Invoke-WebRequest -Uri "http://localhost:9000/minio/health/live" -TimeoutSec 5 -UseBasicParsing
    Write-Host "  ✅ MinIO is healthy`n" -ForegroundColor Green
    $minioHealthy = $true
} catch {
    Write-Host "  ❌ MinIO is not responding`n" -ForegroundColor Red
    $minioHealthy = $false
}

# Summary
Write-Host "=== Verification Summary ===`n" -ForegroundColor Cyan

$totalChecks = $results.Count + $apiResults.Count + 1
$passedChecks = ($results | Where-Object { $_ -eq $true }).Count + ($apiResults | Where-Object { $_ -eq $true }).Count
if ($minioHealthy) { $passedChecks++ }

Write-Host "Health Endpoints: $($results.Count) checks, $($results | Where-Object { $_ -eq $true }).Count passed" -ForegroundColor $(if ($results -contains $false) { "Yellow" } else { "Green" })
Write-Host "API Endpoints: $($apiResults.Count) checks, $($apiResults | Where-Object { $_ -eq $true }).Count passed" -ForegroundColor $(if ($apiResults -contains $false) { "Yellow" } else { "Green" })
Write-Host "Storage: MinIO $($minioHealthy ? "✅ Healthy" : "❌ Unhealthy")" -ForegroundColor $(if ($minioHealthy) { "Green" } else { "Red" })

Write-Host "`nOverall: $passedChecks/$totalChecks checks passed`n" -ForegroundColor $(if ($passedChecks -eq $totalChecks) { "Green" } else { "Yellow" })

if ($passedChecks -eq $totalChecks) {
    Write-Host "🎉 All checks passed! Your Nebula Search deployment is ready." -ForegroundColor Green
    exit 0
} else {
    Write-Host "⚠️  Some checks failed. Review the output above for details." -ForegroundColor Yellow
    Write-Host "`nTroubleshooting:" -ForegroundColor Cyan
    Write-Host "  - Check logs: docker compose -f $ComposeFile logs -f" -ForegroundColor White
    Write-Host "  - Restart services: docker compose -f $ComposeFile restart" -ForegroundColor White
    Write-Host "  - Rebuild: docker compose -f $ComposeFile up -d --force-recreate`n" -ForegroundColor White
    exit 1
}