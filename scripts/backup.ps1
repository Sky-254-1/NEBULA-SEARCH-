n<#
.SYNOPSIS
Comprehensive backup script for Nebula Search Engine with cloud storage integration.

.DESCRIPTION
Creates PostgreSQL database backups with compression, encryption, and optional cloud upload.
Supports retention policies and automated scheduling.

.PARAMETER BackupDir
Directory to store backups. Default: .\database\backups

.PARAMETER RetentionDays
Number of days to keep backups. Default: 30

.PARAMETER Compress
Compress backup files with gzip. Default: true

.PARAMETER Encrypt
Encrypt backup files with AES. Default: false (requires password)

.PARAMETER Password
Encryption password. Required if Encrypt is true.

.PARAMETER UploadToCloud
Upload to cloud storage. Options: none, s3, azure, gcs. Default: none

.PARAMETER CloudBucket
Cloud storage bucket name.

.PARAMETER CloudPath
Path within cloud bucket. Default: nebula-backups

.EXAMPLE
.\backup.ps1 -Compress -RetentionDays 30

.EXAMPLE
.\backup.ps1 -Encrypt -Password "MySecurePassword" -UploadToCloud s3 -CloudBucket "my-backup-bucket"
#>

param(
    [string]$BackupDir = "$PSScriptRoot\..\database\backups",
    [int]$RetentionDays = 30,
    [bool]$Compress = $true,
    [bool]$Encrypt = $false,
    [string]$Password = "",
    [string]$UploadToCloud = "none",
    [string]$CloudBucket = "",
    [string]$CloudPath = "nebula-backups"
)

$ErrorActionPreference = "Stop"
$Script:Root = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $Root "docker\docker-compose.yml"
$ProdCompose = Join-Path $Root "docker-compose.prod.yml"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Date = Get-Date -Format "yyyy-MM-dd"
$BackupName = "nebula_$Timestamp"
$FinalBackupPath = ""

# Ensure backup directory exists
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    Write-Host "[INFO] Created backup directory: $BackupDir" -ForegroundColor Cyan
}

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "NEBULA SEARCH ENGINE - DATABASE BACKUP" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "[INFO] Backup started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "[INFO] Backup directory: $BackupDir" -ForegroundColor Cyan
Write-Host "[INFO] Retention period: $RetentionDays days" -ForegroundColor Cyan

# Step 1: Create PostgreSQL dump
Write-Host "`n[STEP 1/5] Creating PostgreSQL dump..." -ForegroundColor Yellow
$RawBackup = Join-Path $BackupDir "$BackupName.sql"

try {
    docker compose -f $ComposeFile -f $ProdCompose exec -T postgres pg_dump -U nebula nebula > $RawBackup 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump failed with exit code $LASTEXITCODE"
    }
    $RawSize = (Get-Item $RawBackup).Length / 1MB
    Write-Host "[SUCCESS] Dump created: $RawBackup ($([math]::Round($RawSize, 2)) MB)" -ForegroundColor Green
}
catch {
    Write-Host "[FAIL] Database dump failed: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Compress backup
$CurrentBackup = $RawBackup
if ($Compress) {
    Write-Host "`n[STEP 2/5] Compressing backup..." -ForegroundColor Yellow
    try {
        $CompressedFile = Join-Path $BackupDir "$BackupName.sql.gz"
        
        # Use .NET compression
        $inputStream = [System.IO.File]::OpenRead($RawBackup)
        $outputStream = [System.IO.File]::Create($CompressedFile)
        $gzipStream = New-Object System.IO.Compression.GZipStream($outputStream, [System.IO.Compression.CompressionLevel]::Optimal)
        
        $inputStream.CopyTo($gzipStream)
        $gzipStream.Close()
        $outputStream.Close()
        $inputStream.Close()
        
        $CompressedSize = (Get-Item $CompressedFile).Length / 1MB
        $Ratio = [math]::Round((1 - $CompressedSize / $RawSize) * 100, 1)
        
        # Remove uncompressed file
        Remove-Item $RawBackup -ErrorAction SilentlyContinue
        
        Write-Host "[SUCCESS] Compressed: $CompressedFile ($([math]::Round($CompressedSize, 2)) MB, $Ratio% reduction)" -ForegroundColor Green
        $CurrentBackup = $CompressedFile
    }
    catch {
        Write-Host "[WARN] Compression failed: $_" -ForegroundColor Yellow
        Write-Host "[INFO] Keeping uncompressed backup" -ForegroundColor Cyan
    }
}

# Step 3: Encrypt backup
if ($Encrypt) {
    if ([string]::IsNullOrEmpty($Password)) {
        Write-Host "`n[ERROR] Password is required for encryption" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "`n[STEP 3/5] Encrypting backup..." -ForegroundColor Yellow
    try {
        $EncryptedFile = Join-Path $BackupDir "$BackupName.sql.enc"
        
        # Simple AES encryption (for production, use more robust solution)
        $salt = [System.Text.Encoding]::UTF8.GetBytes("NebulaSearchEngine2024")
        $iterations = 10000
        $key = New-Object System.Security.Cryptography.Rfc2898DeriveBytes($Password, $salt, $iterations)
        $aes = [System.Security.Cryptography.Aes]::Create()
        $aes.Key = $key.GetBytes(32)
        $aes.IV = $key.GetBytes(16)
        
        $inputStream = [System.IO.File]::OpenRead($CurrentBackup)
        $outputStream = [System.IO.File]::Create($EncryptedFile)
        $cryptoStream = New-Object System.Security.Cryptography.CryptoStream($outputStream, $aes.CreateEncryptor(), [System.Security.Cryptography.CryptoStreamMode]::Write)
        
        $inputStream.CopyTo($cryptoStream)
        $cryptoStream.FlushFinalBlock()
        
        $cryptoStream.Close()
        $outputStream.Close()
        $inputStream.Close()
        
        # Remove unencrypted file
        Remove-Item $CurrentBackup -ErrorAction SilentlyContinue
        
        Write-Host "[SUCCESS] Encrypted: $EncryptedFile" -ForegroundColor Green
        $CurrentBackup = $EncryptedFile
    }
    catch {
        Write-Host "[WARN] Encryption failed: $_" -ForegroundColor Yellow
    }
}
else {
    Write-Host "`n[STEP 3/5] Skipping encryption (use -Encrypt to enable)" -ForegroundColor DarkGray
}

# Step 4: Upload to cloud storage
$FinalBackupPath = $CurrentBackup
if ($UploadToCloud -ne "none") {
    Write-Host "`n[STEP 4/5] Uploading to $UploadToCloud..." -ForegroundColor Yellow
    
    try {
        switch ($UploadToCloud.ToLower()) {
            "s3" {
                if (-not $CloudBucket) {
                    throw "CloudBucket parameter is required for S3 upload"
                }
                
                $CloudKey = "$CloudPath/$(Split-Path $CurrentBackup -Leaf)"
                Write-Host "[INFO] Uploading to S3: s3://$CloudBucket/$CloudKey" -ForegroundColor Cyan
                
                # Requires AWS CLI installed and configured
                $s3Result = aws s3 cp $CurrentBackup "s3://$CloudBucket/$CloudKey" 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "[SUCCESS] Uploaded to S3" -ForegroundColor Green
                }
                else {
                    throw "S3 upload failed: $s3Result"
                }
            }
            
            "azure" {
                if (-not $CloudBucket) {
                    throw "CloudBucket parameter is required for Azure upload"
                }
                
                $CloudKey = "$CloudPath/$(Split-Path $CurrentBackup -Leaf)"
                Write-Host "[INFO] Uploading to Azure Blob: $CloudBucket/$CloudKey" -ForegroundColor Cyan
                
                # Requires Azure CLI installed and configured
                $azureResult = az storage blob upload `
                    --container-name $CloudBucket `
                    --name $CloudKey `
                    --file $CurrentBackup `
                    --auth-mode login 2>&1
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "[SUCCESS] Uploaded to Azure Blob Storage" -ForegroundColor Green
                }
                else {
                    throw "Azure upload failed: $azureResult"
                }
            }
            
            "gcs" {
                if (-not $CloudBucket) {
                    throw "CloudBucket parameter is required for GCS upload"
                }
                
                $CloudKey = "$CloudPath/$(Split-Path $CurrentBackup -Leaf)"
                Write-Host "[INFO] Uploading to GCS: gs://$CloudBucket/$CloudKey" -ForegroundColor Cyan
                
                # Requires Google Cloud SDK installed and configured
                $gcsResult = gsutil cp $CurrentBackup "gs://$CloudBucket/$CloudKey" 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "[SUCCESS] Uploaded to Google Cloud Storage" -ForegroundColor Green
                }
                else {
                    throw "GCS upload failed: $gcsResult"
                }
            }
            
            default {
                Write-Host "[WARN] Unknown cloud provider: $UploadToCloud" -ForegroundColor Yellow
            }
        }
    }
    catch {
        Write-Host "[WARN] Cloud upload failed: $_" -ForegroundColor Yellow
        Write-Host "[INFO] Backup remains local: $CurrentBackup" -ForegroundColor Cyan
    }
}
else {
    Write-Host "`n[STEP 4/5] Skipping cloud upload (use -UploadToCloud to enable)" -ForegroundColor DarkGray
}

# Step 5: Apply retention policy
Write-Host "`n[STEP 5/5] Applying retention policy ($RetentionDays days)..." -ForegroundColor Yellow
try {
    $CutoffDate = (Get-Date).AddDays(-$RetentionDays)
    $DeletedCount = 0
    $DeletedSize = 0
    
    Get-ChildItem -Path $BackupDir -Filter "nebula_*.sql*" | ForEach-Object {
        if ($_.LastWriteTime -lt $CutoffDate) {
            $DeletedSize += $_.Length
            Remove-Item $_.FullName -Force
            Write-Host "  [DELETED] $($_.Name) ($([math]::Round($_.Length / 1MB, 2)) MB)" -ForegroundColor DarkYellow
            $DeletedCount++
        }
    }
    
    if ($DeletedCount -gt 0) {
        Write-Host "[SUCCESS] Deleted $DeletedCount old backups ($([math]::Round($DeletedSize / 1MB, 2)) MB freed)" -ForegroundColor Green
    }
    else {
        Write-Host "[INFO] No old backups to delete" -ForegroundColor Cyan
    }
}
catch {
    Write-Host "[WARN] Retention policy failed: $_" -ForegroundColor Yellow
}

# Summary
Write-Host "`n" + "=" * 70 -ForegroundColor Cyan
Write-Host "BACKUP SUMMARY" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "[SUCCESS] Backup completed: $FinalBackupPath" -ForegroundColor Green
$FinalSize = (Get-Item $FinalBackupPath -ErrorAction SilentlyContinue).Length / 1MB
Write-Host "[INFO] Final backup size: $([math]::Round($FinalSize, 2)) MB" -ForegroundColor Cyan
Write-Host "[INFO] Backup completed at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "=" * 70

exit 0