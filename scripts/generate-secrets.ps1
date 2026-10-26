#!/usr/bin/env pwsh
# =====================================================================
# Nebula Search - Environment Secret Generator
# =====================================================================
# Generates secure secrets for development and production environments.
# Run this script to create new .env files with cryptographically secure values.
#
# Usage:
#   # Generate development secrets (all optional)
#   .\scripts\generate-secrets.ps1 -Environment development -OutputFile .env.development
#
#   # Generate production secrets (required fields will be flagged)
#   .\scripts\generate-secrets.ps1 -Environment production -OutputFile .env.production
#
#   # Just print secrets to stdout (for CI/CD injection)
#   .\scripts\generate-secrets.ps1 -Environment production -DryRun
# =====================================================================

param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("development", "production")]
    [string]$Environment = "development",

    [Parameter(Mandatory = $false)]
    [string]$OutputFile,

    [Parameter(Mandatory = $false)]
    [switch]$DryRun
)

# =====================================================================
# Secret Generation Functions
# =====================================================================

function Generate-SecureToken([int]$Length = 32) {
    $bytes = [byte[]]::new($Length)
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    return [Convert]::ToBase64String($bytes)
}

function Generate-Base64Secret([int]$Length = 32) {
    return [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Generate-SecureToken $Length)))
}

function Generate-Password([int]$Length = 24) {
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    $bytes = [byte[]]::new($Length)
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    
    $result = New-Object char[] $Length
    for ($i = 0; $i - $Length; $i++) {
        $result[$i] = $chars[$bytes[$i] % $chars.Length]
    }
    return -join $result
}

# =====================================================================
# Required vs Optional Variables
# =====================================================================

$requiredVars = @{
    development = @(
        "APP_ENV",
        "DATABASE_URL"
    )
    production = @(
        "APP_ENV",
        "DATABASE_URL",
        "JWT_SECRET",
        "SESSION_SECRET",
        "ENCRYPTION_KEY"
    )
}

$optionalVars = @(
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_DB",
    "POSTGRES_PORT",
    "REDIS_URL",
    "REDIS_PORT",
    "MINIO_ROOT_USER",
    "MINIO_ROOT_PASSWORD",
    "MINIO_PORT",
    "MINIO_CONSOLE_PORT",
    "BACKEND_PORT",
    "FRONTEND_PORT",
    "CORS_ORIGINS",
    "JWT_EXPIRY_HOURS",
    "JWT_EXPIRY_MINUTES",
    "REFRESH_TOKEN_DAYS",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_MODEL",
    "OLLAMA_URL",
    "OLLAMA_MODEL",
    "STORAGE_ROOT",
    "RATE_LIMIT_PER_MINUTE",
    "LOG_LEVEL",
    "CSP_DEFAULT_SRC",
    "CSP_SCRIPT_SRC",
    "CSP_STYLE_SRC",
    "CSP_IMG_SRC",
    "CSP_CONNECT_SRC",
    "CSP_FONT_SRC",
    "CSP_FRAME_SRC",
    "CSP_OBJECT_SRC",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
    "GOOGLE_OAUTH2_CLIENT_ID",
    "GOOGLE_OAUTH2_CLIENT_SECRET",
    "GITHUB_OAUTH2_CLIENT_ID",
    "GITHUB_OAUTH2_CLIENT_SECRET",
    "SENTRY_DSN",
    "ELASTICSEARCH_URL",
    "RABBITMQ_USER",
    "RABBITMQ_PASSWORD",
    "KAFKA_BOOTSTRAP_SERVERS"
)

# =====================================================================
# Generate Secrets
# =====================================================================

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Nebula Search - Secret Generator" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Generate secure secrets
$secrets = @{
    JWT_SECRET              = Generate-SecureToken 32
    SESSION_SECRET          = Generate-SecureToken 32
    ENCRYPTION_KEY          = Generate-SecureToken 32
    POSTGRES_PASSWORD       = Generate-Password 24
    MINIO_ROOT_PASSWORD     = Generate-Password 24
    GRAFANA_ADMIN_PASSWORD  = Generate-Password 16
    RABBITMQ_PASSWORD       = Generate-Password 20
}

# =====================================================================
# Output Results
# =====================================================================

if ($DryRun -or -not $OutputFile) {
    Write-Host "Generated Secrets (not saved to file):" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor Yellow
}

$template = @(
    "# =====================================================================",
    "# Nebula Search Environment Configuration",
    "# =====================================================================",
    "# Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "# Environment: $Environment",
    "#",
    "# IMPORTANT: Copy this file to .env and fill in your values.",
    "# DO NOT commit .env files to version control!",
    "# =====================================================================",
    ""
)

# Add required vars
foreach ($var in $requiredVars.$Environment) {
    $template += "# REQUIRED: $var"
    if ($var -eq "APP_ENV") {
        $template += "APP_ENV=$Environment"
    } elseif ($var -eq "DATABASE_URL") {
        $template += "DATABASE_URL=nebula.db"
        if ($Environment -eq "production") {
            $template += "# For production, use PostgreSQL URL:"
            $template += "# DATABASE_URL=postgresql://user:password@host:5432/database"
        }
    }
    $template += ""
}

# Add optional vars
foreach ($var in $optionalVars) {
    $template += "# Optional: $var"
    if ($secrets.ContainsKey($var)) {
        $template += "$var=$($secrets[$var])"
    } elseif ($var -match "PASSWORD" -or $var -match "SECRET" -or $var -match "KEY") {
        $template += "$var=change-me-in-production"
    } else {
        $template += "$var="
    }
    $template += ""
}

# Add production-specific vars
if ($Environment -eq "production") {
    $template += "# ====================================================================="
    $template += "# PRODUCTION-SPECIFIC CONFIGURATION"
    $template += "# ====================================================================="
    $template += "# CORS must be explicit (no wildcards when using credentials)"
    $template += "CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com"
    $template += ""
    $template += "# In production, set secure cookie options"
    $template += "COOKIE_SECURE=true"
    $template += "COOKIE_SAMESITE=strict"
    $template += ""
}

# Output to file or stdout
if ($OutputFile) {
    $template | Set-Content -Path $OutputFile -Encoding utf8
    Write-Host "Generated environment file saved to: $OutputFile" -ForegroundColor Green
} else {
    $template | ForEach-Object { Write-Host $_ }
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Copy this file to .env:$Environment"
Write-Host "2. Replace placeholder values with your actual credentials"
Write-Host "3. Never commit .env files to version control"
Write-Host "4. For production: rotate all secrets through their providers"
Write-Host "==================================================" -ForegroundColor Cyan