#!/bin/bash
set -euo pipefail

# Nebula Search Engine - Database Restore Script
# Usage: ./restore.sh <backup_file> [postgres|redis|minio]
# The backup type is inferred from the filename

BACKUP_FILE="${1:-}"
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 backups/postgres_20240101_120000.sql.gz"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Load environment variables
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
elif [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "==================================="
echo "Nebula Restore"
echo "==================================="
echo "Backup file: $BACKUP_FILE"

# Determine backup type from filename
if [[ "$BACKUP_FILE" == *"postgres"* ]]; then
    echo "Detected: PostgreSQL backup"
    
    echo "WARNING: This will overwrite the current database!"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Restore cancelled"
        exit 0
    fi
    
    echo "Restoring PostgreSQL..."
    
    # Drop and recreate database
    docker exec nebula-postgres psql -U ${POSTGRES_USER:-nebula} -c "DROP DATABASE IF EXISTS ${POSTGRES_DB:-nebula};"
    docker exec nebula-postgres psql -U ${POSTGRES_USER:-nebula} -c "CREATE DATABASE ${POSTGRES_DB:-nebula};"
    
    # Restore from backup
    gunzip -c "$BACKUP_FILE" | docker exec -i nebula-postgres psql -U ${POSTGRES_USER:-nebula} ${POSTGRES_DB:-nebula}
    
    echo "✓ PostgreSQL restore completed"
    
elif [[ "$BACKUP_FILE" == *"redis"* ]]; then
    echo "Detected: Redis backup"
    
    echo "WARNING: This will overwrite the current Redis data!"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Restore cancelled"
        exit 0
    fi
    
    echo "Restoring Redis..."
    
    # Stop Redis temporarily
    docker stop nebula-redis
    
    # Copy backup file to container
    gunzip -c "$BACKUP_FILE" > /tmp/dump.rdb
    docker cp /tmp/dump.rdb nebula-redis:/data/dump.rdb
    rm /tmp/dump.rdb
    
    # Start Redis
    docker start nebula-redis
    
    echo "✓ Redis restore completed"
    
elif [[ "$BACKUP_FILE" == *"minio"* ]]; then
    echo "Detected: MinIO backup"
    
    echo "WARNING: This will overwrite the current MinIO data!"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Restore cancelled"
        exit 0
    fi
    
    echo "Restoring MinIO..."
    
    # Stop MinIO temporarily
    docker stop nebula-storage
    
    # Extract backup to MinIO data directory
    docker run --rm \
        --volumes-from nebula-storage \
        -v "$(pwd)/backups:/backup" \
        alpine sh -c "rm -rf /data/* && tar xzf /backup/$(basename "$BACKUP_FILE") -C /data"
    
    # Start MinIO
    docker start nebula-storage
    
    echo "✓ MinIO restore completed"
    
else
    echo "Error: Could not determine backup type from filename"
    echo "Backup file should contain 'postgres', 'redis', or 'minio' in the name"
    exit 1
fi

echo "==================================="
echo "Restore completed successfully"
echo "==================================="
echo "Please verify the restored data and restart services if needed."