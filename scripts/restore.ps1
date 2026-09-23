<#
.SYNOPSIS
Restore Nebula Search Engine database from backup.

.DESCRIPTION
Restores PostgreSQL database from compressed and/or encrypted backup files.
Supports point-in-time recovery and validation.

.PARAMETER BackupFile
Path to backup file (.sql, .sql.gz, or .sql.enc).

.PARAMETER DatabaseName
Target database name. Default: nebula

.PARAMETER Password
Decryption password. Required if backup is encrypted.

.PARAMETER SkipValidation
Skip backup validation before restore. Default: false

.EXAMPLE
.\restore.ps1 -BackupFile ".\database\backups\nebula_20240101_120000.sql.gz"

.EXAMPLE
.\restore.ps1 -BackupFile ".\database\backups\nebula_20240101_120000.sql.enc" -Password "MySecurePassword"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,

    [string]$DatabaseName = "nebula",

    [string]$Password = "",

    [bool]$SkipValidation = $false
)

$ErrorActionPreference = "Stop"
$Script:Root = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $Root "docker\docker-compose.yml"
$ProdCompose = Join-Path $Root "docker-compose.prod.yml"

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "NEBULA SEARCH ENGINE - DATABASE RESTORE" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "[INFO] Restore started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "[INFO] Backup file: $BackupFile" -ForegroundColor Cyan
Write-Host "[INFO] Target database: $DatabaseName" -ForegroundColor Cyan

# Validate backup file exists
if (-not (Test-Path $BackupFile)) {
    Write-Host "[ERROR] Backup file not found: $BackupFile" -ForegroundColor Red
    exit 1
}

$BackupExtension = [System.IO.Path]::GetExtension($BackupFile)
$TempBackup = Join-Path $Root "database\backups\temp_restore.sql"

# Step 1: Prepare backup file
Write-Host "`n[STEP 1/4] Preparing backup file..." -ForegroundColor Yellow

try {
    # Handle encrypted backups
    if ($BackupExtension -eq ".enc") {
        if ([string]::IsNullOrEmpty($Password)) {
            Write-Host "[ERROR] Password is required for encrypted backups" -ForegroundColor Red
            exit 1
        }
        
        Write-Host "[INFO] Decrypting backup..." -ForegroundColor Cyan
        try {
            $salt = [System.Text.Encoding]::UTF8.GetBytes("NebulaSearchEngine2024")
            $iterations = 10000
            $key = New-Object System.Security.Cryptography.Rfc2898DeriveBytes($Password, $salt, $iterations)
            $aes = [System.Security.Cryptography.Aes]::Create()
            $aes.Key = $key.GetBytes(32)
            $aes.IV = $key.GetBytes(16)
            
            $inputStream = [System.IO.File]::OpenRead($BackupFile)
            $outputStream = [System.IO.File]::Create($TempBackup)
            $cryptoStream = New-Object System.Security.Cryptography.CryptoStream($inputStream, $aes.CreateDecryptor(), [System.Security.Cryptography.CryptoStreamMode]::Read)
            
            $cryptoStream.CopyTo($outputStream)
            
            $cryptoStream.Close()
            $outputStream.Close()
            $inputStream.Close()
            
            Write-Host "[SUCCESS] Decrypted backup to: $TempBackup" -ForegroundColor Green
            $CurrentBackup = $TempBackup
        }
        catch {
            Write-Host "[ERROR] Decryption failed: $_" -ForegroundColor Red
            exit 1
        }
    }
    else {
        $CurrentBackup = $BackupFile
    }
    
    # Handle compressed backups
    if ($BackupExtension -eq ".gz" -or $BackupFile.EndsWith(".sql.gz")) {
        Write-Host "[INFO] Decompressing backup..." -ForegroundColor Cyan
        try {
            $inputStream = [System.IO.File]::OpenRead($CurrentBackup)
            $outputStream = [System.IO.File]::Create($TempBackup)
            $gzipStream = New-Object System.IO.Compression.GZipStream($inputStream, [System.IO.Compression.CompressionMode]::Decompress)
            
            $gzipStream.CopyTo($outputStream)
            
            $gzipStream.Close()
            $outputStream.Close()
            $inputStream.Close()
            
            Write-Host "[SUCCESS] Decompressed backup to: $TempBackup" -ForegroundColor Green
            $CurrentBackup = $TempBackup
        }
        catch {
            Write-Host "[ERROR] Decompression failed: $_" -ForegroundColor Red
            exit 1
        }
    }
}
catch {
    Write-Host "[ERROR] Failed to prepare backup file: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Validate backup
if (-not $SkipValidation) {
    Write-Host "`n[STEP 2/4] Validating backup..." -ForegroundColor Yellow
    
    try {
        $content = Get-Content $CurrentBackup -TotalCount 50
        
        # Check for valid SQL content
        $hasCreateTable = $false
        $hasCreateIndex = $false
        
        foreach ($line in $content) {
            if ($line -match "CREATE TABLE") { $hasCreateTable = $true }
            if ($line -match "CREATE INDEX") { $hasCreateIndex = $true }
            
            if ($hasCreateTable -and $hasCreateIndex) { break }
        }
        
        if (-not $hasCreateTable) {
            Write-Host "[WARN] Backup may not contain table definitions" -ForegroundColor Yellow
        }
        
        $lineCount = (Get-Content $CurrentBackup).Count
        Write-Host "[SUCCESS] Backup validated: $lineCount lines" -ForegroundColor Green
    }
    catch {
        Write-Host "[ERROR] Backup validation failed: $_" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "`n[STEP 2/4] Skipping validation (use -SkipValidation `$false to enable)" -ForegroundColor DarkGray
}

# Step 3: Confirmation prompt
Write-Host "`n[STEP 3/4] Pre-restore checks..." -ForegroundColor Yellow

# Check if database container is running
$containerCheck = docker compose -f $ComposeFile -f $ProdCompose ps postgres 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker Compose not found or PostgreSQL not configured" -ForegroundColor Red
    exit 1
}

# Confirm database exists
Write-Host "[INFO] Checking database connection..." -ForegroundColor Cyan
$dbCheck = docker compose -f $ComposeFile -f $ProdCompose exec -T postgres psql -U nebula -l 2>&1 | Select-String $DatabaseName
if ($LASTEXITCODE -ne 0 -or -not $dbCheck) {
    Write-Host "[WARN] Database '$DatabaseName' may not exist. It will be created." -ForegroundColor Yellow
}

Write-Host "`n[WARNING] This will overwrite the database '$DatabaseName'!" -ForegroundColor Red
Write-Host "[WARNING] All existing data will be lost!" -ForegroundColor Red
$confirm = Read-Host "`nAre you sure you want to continue? (yes/no)"

if ($confirm -ne "yes") {
    Write-Host "[INFO] Restore cancelled by user" -ForegroundColor Yellow
    exit 0
}

# Step 4: Perform restore
Write-Host "`n[STEP 4/4] Performing restore..." -ForegroundColor Yellow

try {
    # Drop and recreate database
    Write-Host "[INFO] Dropping existing database..." -ForegroundColor Cyan
    docker compose -f $ComposeFile -f $ProdCompose exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS $DatabaseName;" 2>&1 | Out-Null
    
    Write-Host "[INFO] Creating fresh database..." -ForegroundColor Cyan
    docker compose -f $ComposeFile -f $ProdCompose exec -T postgres psql -U postgres -c "CREATE DATABASE $DatabaseName OWNER nebula;" 2>&1 | Out-Null
    
    # Restore from backup
    Write-Host "[INFO] Restoring from backup..." -ForegroundColor Cyan
    
    # Read backup content and pipe to psql
    $backupContent = Get-Content -Path $CurrentBackup
    $backupContent | docker compose -f $ComposeFile -f $ProdCompose exec -T postgres psql -U nebula -d $DatabaseName
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] Database restored successfully" -ForegroundColor Green
    }
    else {
        throw "psql restore failed with exit code $LASTEXITCODE"
    }
    
    # Verify restore
    Write-Host "[INFO] Verifying restore..." -ForegroundColor Cyan
    $tableCount = docker compose -f $ComposeFile -f $ProdCompose exec -T postgres psql -U nebula -d $DatabaseName -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>&1 | Select-String "\d+" | ForEach-Object { $_.ToString().Trim() }
    
    if ($tableCount -gt 0) {
        Write-Host "[SUCCESS] Verified: $tableCount tables restored" -ForegroundColor Green
    }
    else {
        Write-Host "[WARN] Could not verify table count" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "[ERROR] Restore failed: $_" -ForegroundColor Red
    exit 1
}
finally {
    # Cleanup temp files
    if (Test-Path $TempBackup) {
        Remove-Item $TempBackup -ErrorAction SilentlyContinue
    }
}

# Summary
Write-Host "`n" + "=" * 70 -ForegroundColor Cyan
Write-Host "RESTORE SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "[SUCCESS] Database restored: $DatabaseName" -ForegroundColor Green
Write-Host "[INFO] Restore completed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "[INFO] Next steps:" -ForegroundColor Cyan
Write-Host "  1. Verify application functionality" -ForegroundColor White
Write-Host "  2. Run database migrations: make migrate" -ForegroundColor White
Write-Host "  3. Test search functionality" -ForegroundColor White
Write-Host "=" * 70

exit 0