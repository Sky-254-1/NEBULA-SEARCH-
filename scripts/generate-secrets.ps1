# Generate secure secrets for .env.production
# Run this script to create strong random secrets

param(
    [switch]$UpdateEnvFile = $false,
    [string]$EnvFilePath = "..\.env.production"
)

function New-RandomSecret {
    param([int]$Length = 32)
    
    if ($Length -lt 32) {
        Write-Warning "For security, secrets should be at least 32 characters"
    }
    
    # Use .NET's RNGCryptoServiceProvider for cryptographically secure random bytes
    $bytes = New-Object byte[] $Length
    $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::new()
    $rng.GetBytes($bytes)
    $rng.Dispose()
    
    # Convert to URL-safe base64
    return [Convert]::ToBase64String($bytes) -replace '\+', '-' -replace '/', '_' -replace '=', ''
}

Write-Host "`n=== Nebula Search - Secret Generator ===`n" -ForegroundColor Cyan

$secrets = @{
    "JWT_SECRET" = New-RandomSecret -Length 32
    "SESSION_SECRET" = New-RandomSecret -Length 32
    "ENCRYPTION_KEY" = New-RandomSecret -Length 32
    "POSTGRES_PASSWORD" = New-RandomSecret -Length 24
    "MINIO_ROOT_PASSWORD" = New-RandomSecret -Length 24
    "GRAFANA_ADMIN_PASSWORD" = New-RandomSecret -Length 24
}

Write-Host "Generated Secrets (save these securely):`n" -ForegroundColor Yellow
$secrets.GetEnumerator() | ForEach-Object {
    Write-Host "$($_.Key)=" -NoNewline -ForegroundColor Gray
    Write-Host $_.Value -ForegroundColor Green
}

if ($UpdateEnvFile) {
    if (-not (Test-Path $EnvFilePath)) {
        Write-Host "`nCreating $EnvFilePath from .env.example..." -ForegroundColor Yellow
        Copy-Item "..\.env.example" $EnvFilePath
    }
    
    Write-Host "`nUpdating $EnvFilePath with generated secrets..." -ForegroundColor Yellow
    
    $envContent = Get-Content $EnvFilePath -Raw
    
    foreach ($secret in $secrets.GetEnumerator()) {
        $pattern = "$($secret.Key)=.*"
        $replacement = "$($secret.Key)=$($secret.Value)"
        $envContent = [Regex]::Replace($envContent, $pattern, $replacement)
    }
    
    $envContent | Set-Content $EnvFilePath -NoNewline
    Write-Host "✅ Updated $EnvFilePath" -ForegroundColor Green
    Write-Host "⚠️  Keep this file secure and never commit it to version control!" -ForegroundColor Red
} else {
    Write-Host "`nTo update .env.production automatically, run:" -ForegroundColor Cyan
    Write-Host "  .\generate-secrets.ps1 -UpdateEnvFile`n" -ForegroundColor White
}

# Also output as export commands for Linux/macOS
Write-Host "`n=== Export Commands (Linux/macOS) ===`n" -ForegroundColor Cyan
$secrets.GetEnumerator() | ForEach-Object {
    Write-Host "export $($_.Key)=$($_.Value)"
}