#!/bin/bash
set -euo pipefail

# Nebula Search Engine - Database Backup Script
# Creates PostgreSQL backups with compression, encryption, and cloud storage integration

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${ROOT_DIR}/database/backups"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
COMPRESS="${COMPRESS:-true}"
ENCRYPT="${ENCRYPT:-false}"
PASSWORD="${BACKUP_PASSWORD:-}"
UPLOAD_TO_CLOUD="${UPLOAD_TO_CLOUD:-none}"
CLOUD_BUCKET="${CLOUD_BUCKET:-}"
CLOUD_PATH="${CLOUD_PATH:-nebula-backups}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="nebula_${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

echo "=================================================="
echo -e "${CYAN}NEBULA SEARCH ENGINE - DATABASE BACKUP${NC}"
echo "=================================================="
echo -e "${CYAN}[INFO]${NC} Backup started at: $(date '+%Y-%m-%d %H:%M:%S')"
echo -e "${CYAN}[INFO]${NC} Backup directory: $BACKUP_DIR"
echo -e "${CYAN}[INFO]${NC} Retention period: $RETENTION_DAYS days"

# Step 1: Create PostgreSQL dump
echo -e "\n${YELLOW}[STEP 1/5] Creating PostgreSQL dump...${NC}"
RAW_BACKUP="${BACKUP_DIR}/${BACKUP_NAME}.sql"

if docker compose -f "${ROOT_DIR}/docker/docker-compose.yml" -f "${ROOT_DIR}/docker-compose.prod.yml" exec -T postgres pg_dump -U nebula nebula > "$RAW_BACKUP" 2>&1; then
    RAW_SIZE=$(du -h "$RAW_BACKUP" | cut -f1)
    echo -e "${GREEN}[SUCCESS]${NC} Dump created: $RAW_BACKUP ($RAW_SIZE)"
else
    echo -e "${RED}[FAIL]${NC} Database dump failed"
    rm -f "$RAW_BACKUP"
    exit 1
fi

# Step 2: Compress backup
CURRENT_BACKUP="$RAW_BACKUP"
if [ "$COMPRESS" = "true" ]; then
    echo -e "\n${YELLOW}[STEP 2/5] Compressing backup...${NC}"
    COMPRESSED_FILE="${BACKUP_DIR}/${BACKUP_NAME}.sql.gz"
    
    if gzip -c "$RAW_BACKUP" > "$COMPRESSED_FILE"; then
        COMPRESSED_SIZE=$(du -h "$COMPRESSED_FILE" | cut -f1)
        RAW_SIZE_MB=$(du -m "$RAW_BACKUP" | cut -f1)
        COMPRESSED_SIZE_MB=$(du -m "$COMPRESSED_FILE" | cut -f1)
        RATIO=$(( (RAW_SIZE_MB - COMPRESSED_SIZE_MB) * 100 / RAW_SIZE_MB ))
        
        rm -f "$RAW_BACKUP"
        echo -e "${GREEN}[SUCCESS]${NC} Compressed: $COMPRESSED_FILE ($COMPRESSED_SIZE, ${RATIO}% reduction)"
        CURRENT_BACKUP="$COMPRESSED_FILE"
    else
        echo -e "${YELLOW}[WARN]${NC} Compression failed, keeping uncompressed backup"
    fi
else
    echo -e "\n${YELLOW}[STEP 2/5]${NC} Skipping compression"
fi

# Step 3: Encrypt backup
if [ "$ENCRYPT" = "true" ]; then
    if [ -z "$PASSWORD" ]; then
        echo -e "\n${RED}[ERROR]${NC} Password is required for encryption"
        exit 1
    fi
    
    echo -e "\n${YELLOW}[STEP 3/5] Encrypting backup...${NC}"
    ENCRYPTED_FILE="${BACKUP_DIR}/${BACKUP_NAME}.sql.enc"
    
    # Simple AES encryption using OpenSSL
    if openssl enc -aes-256-cbc -salt -pbkdf2 -in "$CURRENT_BACKUP" -out "$ENCRYPTED_FILE" -pass "pass:$PASSWORD" 2>&1; then
        rm -f "$CURRENT_BACKUP"
        echo -e "${GREEN}[SUCCESS]${NC} Encrypted: $ENCRYPTED_FILE"
        CURRENT_BACKUP="$ENCRYPTED_FILE"
    else
        echo -e "${YELLOW}[WARN]${NC} Encryption failed"
    fi
else
    echo -e "\n${YELLOW}[STEP 3/5]${NC} Skipping encryption (set ENCRYPT=true to enable)"
fi

# Step 4: Upload to cloud storage
if [ "$UPLOAD_TO_CLOUD" != "none" ]; then
    echo -e "\n${YELLOW}[STEP 4/5] Uploading to $UPLOAD_TO_CLOUD...${NC}"
    
    case "$UPLOAD_TO_CLOUD" in
        s3)
            if [ -z "$CLOUD_BUCKET" ]; then
                echo -e "${RED}[ERROR]${NC} CLOUD_BUCKET is required for S3 upload"
            else
                CLOUD_KEY="${CLOUD_PATH}/$(basename "$CURRENT_BACKUP")"
                echo -e "${CYAN}[INFO]${NC} Uploading to S3: s3://$CLOUD_BUCKET/$CLOUD_KEY"
                
                if aws s3 cp "$CURRENT_BACKUP" "s3://$CLOUD_BUCKET/$CLOUD_KEY" 2>&1; then
                    echo -e "${GREEN}[SUCCESS]${NC} Uploaded to S3"
                else
                    echo -e "${YELLOW}[WARN]${NC} S3 upload failed"
                fi
            fi
            ;;
            
        azure)
            if [ -z "$CLOUD_BUCKET" ]; then
                echo -e "${RED}[ERROR]${NC} CLOUD_BUCKET is required for Azure upload"
            else
                CLOUD_KEY="${CLOUD_PATH}/$(basename "$CURRENT_BACKUP")"
                echo -e "${CYAN}[INFO]${NC} Uploading to Azure Blob: $CLOUD_BUCKET/$CLOUD_KEY"
                
                if az storage blob upload \
                    --container-name "$CLOUD_BUCKET" \
                    --name "$CLOUD_KEY" \
                    --file "$CURRENT_BACKUP" \
                    --auth-mode login 2>&1; then
                    echo -e "${GREEN}[SUCCESS]${NC} Uploaded to Azure Blob Storage"
                else
                    echo -e "${YELLOW}[WARN]${NC} Azure upload failed"
                fi
            fi
            ;;
            
        gcs)
            if [ -z "$CLOUD_BUCKET" ]; then
                echo -e "${RED}[ERROR]${NC} CLOUD_BUCKET is required for GCS upload"
            else
                CLOUD_KEY="${CLOUD_PATH}/$(basename "$CURRENT_BACKUP")"
                echo -e "${CYAN}[INFO]${NC} Uploading to GCS: gs://$CLOUD_BUCKET/$CLOUD_KEY"
                
                if gsutil cp "$CURRENT_BACKUP" "gs://$CLOUD_BUCKET/$CLOUD_KEY" 2>&1; then
                    echo -e "${GREEN}[SUCCESS]${NC} Uploaded to Google Cloud Storage"
                else
                    echo -e "${YELLOW}[WARN]${NC} GCS upload failed"
                fi
            fi
            ;;
            
        *)
            echo -e "${YELLOW}[WARN]${NC} Unknown cloud provider: $UPLOAD_TO_CLOUD"
            ;;
    esac
else
    echo -e "\n${YELLOW}[STEP 4/5]${NC} Skipping cloud upload (set UPLOAD_TO_CLOUD to enable)"
fi

# Step 5: Apply retention policy
echo -e "\n${YELLOW}[STEP 5/5] Applying retention policy ($RETENTION_DAYS days)...${NC}"
CUTOFF_DATE=$(date -d "-${RETENTION_DAYS} days" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || date -v-${RETENTION_DAYS}d '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "1970-01-01")

DELETED_COUNT=0
DELETED_SIZE=0

for backup_file in "$BACKUP_DIR"/nebula_*.sql*; do
    if [ -f "$backup_file" ]; then
        FILE_DATE=$(stat -c '%Y' "$backup_file" 2>/dev/null || stat -f '%m' "$backup_file" 2>/dev/null || echo "0")
        CURRENT_DATE=$(date '+%s')
        FILE_AGE_DAYS=$(( (CURRENT_DATE - FILE_DATE) / 86400 ))
        
        if [ "$FILE_AGE_DAYS" -gt "$RETENTION_DAYS" ]; then
            FILE_SIZE=$(du -m "$backup_file" | cut -f1)
            DELETED_SIZE=$((DELETED_SIZE + FILE_SIZE))
            rm -f "$backup_file"
            echo -e "  ${YELLOW}[DELETED]${NC} $(basename "$backup_file") (${FILE_SIZE} MB)"
            DELETED_COUNT=$((DELETED_COUNT + 1))
        fi
    fi
done

if [ "$DELETED_COUNT" -gt 0 ]; then
    echo -e "${GREEN}[SUCCESS]${NC} Deleted $DELETED_COUNT old backups (${DELETED_SIZE} MB freed)"
else
    echo -e "${CYAN}[INFO]${NC} No old backups to delete"
fi

# Summary
echo -e "\n=================================================="
echo -e "${CYAN}BACKUP SUMMARY${NC}"
echo "=================================================="
echo -e "${GREEN}[SUCCESS]${NC} Backup completed: $CURRENT_BACKUP"
FINAL_SIZE=$(du -h "$CURRENT_BACKUP" | cut -f1)
echo -e "${CYAN}[INFO]${NC} Final backup size: $FINAL_SIZE"
echo -e "${CYAN}[INFO]${NC} Backup completed at: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================="

exit 0