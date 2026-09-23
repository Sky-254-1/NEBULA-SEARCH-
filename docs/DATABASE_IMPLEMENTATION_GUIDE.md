# IOIS (Nebula) - Database Implementation Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Database Setup](#database-setup)
5. [Running Migrations](#running-migrations)
6. [Seeding Data](#seeding-data)
7. [Verification](#verification)
8. [Development Workflow](#development-workflow)
9. [Testing](#testing)
10. [Deployment](#deployment)
11. [Troubleshooting](#troubleshooting)
12. [Best Practices](#best-practices)

---

## Prerequisites

### Required Software

- **PostgreSQL 15+**: Database server
  ```bash
  # Ubuntu/Debian
  sudo apt-get install postgresql-15 postgresql-contrib-15
  
  # macOS
  brew install postgresql@15
  
  # Windows
  # Download from https://www.postgresql.org/download/windows/
  ```

- **psql**: PostgreSQL command-line client
  ```bash
  # Usually installed with PostgreSQL
  psql --version
  ```

- **Python 3.9+**: For migration scripts (optional)
  ```bash
  python --version
  ```

### Required Knowledge

- Basic SQL syntax
- PostgreSQL administration
- Database design concepts
- Command-line operations

---

## Installation

### 1. Install PostgreSQL

#### Ubuntu/Debian

```bash
# Add PostgreSQL repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# Install PostgreSQL 15
sudo apt-get update
sudo apt-get install postgresql-15 postgresql-contrib-15

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### macOS

```bash
# Install using Homebrew
brew install postgresql@15

# Start PostgreSQL
brew services start postgresql@15

# Verify installation
psql --version
```

#### Windows

```powershell
# Download installer from https://www.postgresql.org/download/windows/
# Run installer and follow prompts
# Remember the password you set for postgres user

# Add to PATH (if needed)
$env:Path += ";C:\Program Files\PostgreSQL\15\bin"
```

### 2. Verify Installation

```bash
# Check PostgreSQL version
psql --version

# Connect to PostgreSQL as postgres user
sudo -u postgres psql -c "SELECT version();"

# Expected output: PostgreSQL 15.x on ...
```

---

## Configuration

### 1. Create Database User

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database user
CREATE ROLE nebula_admin WITH 
    LOGIN 
    SUPERUSER 
    CREATEDB 
    CREATEROLE 
    PASSWORD 'your_secure_password_here';

# Create application user (for app connections)
CREATE ROLE nebula_app WITH 
    LOGIN 
    NOSUPERUSER 
    NOCREATEDB 
    NOCREATEROLE 
    PASSWORD 'app_secure_password_here';

# Grant permissions
GRANT CONNECT ON DATABASE nebula_db TO nebula_app;
GRANT USAGE ON SCHEMA public, auth, search, analytics, notifications, storage, audit, admin TO nebula_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public, auth, search, analytics, notifications, storage, audit, admin TO nebula_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public, auth, search, analytics, notifications, storage, audit, admin TO nebula_app;

# Exit
\q
```

### 2. Create Database

```bash
# Create database
sudo -u postgres createdb -O nebula_admin nebula_db

# Verify database exists
sudo -u postgres psql -l
```

### 3. Configure PostgreSQL Settings

Edit `postgresql.conf`:

```bash
# Find configuration file location
sudo -u postgres psql -c "SHOW config_file;"

# Edit configuration
sudo nano /etc/postgresql/15/main/postgresql.conf
```

Add/modify these settings:

```ini
# Connection Settings
listen_addresses = 'localhost'
port = 5432
max_connections = 100
superuser_reserved_connections = 3

# Memory Settings
shared_buffers = 256MB
work_mem = 64MB
maintenance_work_mem = 128MB
effective_cache_size = 1GB

# WAL Settings
wal_level = replica
max_wal_senders = 10
wal_keep_size = 1GB

# Query Tuning
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d.log'
log_rotation_age = 1d
log_rotation_size = 100MB
log_min_duration_statement = 1000
log_connections = on
log_disconnections = on
log_lock_waits = on

# Timezone
timezone = 'UTC'
log_timezone = 'UTC'
```

Edit `pg_hba.conf`:

```bash
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

Add these lines:

```ini
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# Local connections
local   all             postgres                                peer
local   all             nebula_admin                             md5
local   all             nebula_app                               md5

# IPv4 local connections
host    all             all             127.0.0.1/32            md5

# IPv6 local connections
host    all             all             ::1/128                 md5
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### 4. Install Extensions

```bash
# Connect to database
sudo -u postgres psql -d nebula_db

# Install required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

# Verify extensions
\dx

# Expected output should include:
# - uuid-ossp
# - pgcrypto
# - btree_gin
# - pg_trgm

# Exit
\q
```

---

## Database Setup

### Option 1: Using Migration Scripts (Recommended)

```bash
# Navigate to project directory
cd /path/to/nebula-search-engine

# Run initial migration
psql -U nebula_admin -d nebula_db -f database/schema/001_initial_schema.sql

# Expected output: Schema created successfully
```

### Option 2: Using Python Migration Script

Create `database/scripts/migrate.py`:

```python
#!/usr/bin/env python3
"""
Database migration runner script
"""

import os
import sys
import glob
import subprocess
from pathlib import Path

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'nebula_db',
    'user': 'nebula_admin',
    'password': os.getenv('DB_PASSWORD', 'your_secure_password_here')
}

def run_migration(file_path: str) -> bool:
    """Run a single migration file"""
    print(f"Running migration: {file_path}")
    
    try:
        result = subprocess.run(
            [
                'psql',
                '-h', DB_CONFIG['host'],
                '-p', str(DB_CONFIG['port']),
                '-U', DB_CONFIG['user'],
                '-d', DB_CONFIG['database'],
                '-f', file_path,
                '-v', 'ON_ERROR_STOP=1'
            ],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, 'PGPASSWORD': DB_CONFIG['password']}
        )
        print(f"✓ Success: {file_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {file_path}")
        print(f"Error: {e.stderr}")
        return False

def run_seed(file_path: str) -> bool:
    """Run a single seed file"""
    print(f"Seeding: {file_path}")
    
    try:
        result = subprocess.run(
            [
                'psql',
                '-h', DB_CONFIG['host'],
                '-p', str(DB_CONFIG['port']),
                '-U', DB_CONFIG['user'],
                '-d', DB_CONFIG['database'],
                '-f', file_path,
                '-v', 'ON_ERROR_STOP=1'
            ],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, 'PGPASSWORD': DB_CONFIG['password']}
        )
        print(f"✓ Success: {file_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {file_path}")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main migration runner"""
    print("=" * 60)
    print("IOIS (Nebula) Database Migration Runner")
    print("=" * 60)
    
    # Run migrations
    migration_files = sorted(glob.glob('database/schema/*.sql'))
    print(f"\nFound {len(migration_files)} migration files")
    
    migration_success = True
    for migration_file in migration_files:
        if not run_migration(migration_file):
            migration_success = False
            print("\n❌ Migration failed. Stopping.")
            sys.exit(1)
    
    if migration_success:
        print("\n✓ All migrations completed successfully")
    
    # Run seeds
    seed_files = sorted(glob.glob('database/seeds/*.sql'))
    print(f"\nFound {len(seed_files)} seed files")
    
    seed_success = True
    for seed_file in seed_files:
        if not run_seed(seed_file):
            seed_success = False
            print("\n❌ Seeding failed. Stopping.")
            sys.exit(1)
    
    if seed_success:
        print("\n✓ All seeds completed successfully")
    
    print("\n" + "=" * 60)
    print("Database setup completed successfully!")
    print("=" * 60)

if __name__ == '__main__':
    main()
```

Make it executable:

```bash
chmod +x database/scripts/migrate.py
```

Run migrations:

```bash
# Set database password
export DB_PASSWORD='your_secure_password_here'

# Run migrations and seeds
python database/scripts/migrate.py
```

### Option 3: Using Docker

```bash
# If using Docker Compose
docker-compose exec db psql -U nebula_admin -d nebula_db -f /migrations/001_initial_schema.sql

# Or run all migrations
for file in database/schema/*.sql; do
    docker-compose exec db psql -U nebula_admin -d nebula_db -f "/migrations/$(basename $file)"
done
```

---

## Running Migrations

### Manual Migration Execution

```bash
# Run single migration file
psql -U nebula_admin -d nebula_db -f database/schema/001_initial_schema.sql

# Run with password prompt
psql -U nebula_admin -d nebula_db -W -f database/schema/001_initial_schema.sql

# Run with password in environment variable
PGPASSWORD='your_password' psql -U nebula_admin -d nebula_db -f database/schema/001_initial_schema.sql
```

### Batch Migration Execution

```bash
#!/bin/bash
# run_migrations.sh

set -e  # Exit on error

echo "Running database migrations..."

for file in database/schema/*.sql; do
    if [ -f "$file" ]; then
        echo "Running: $file"
        PGPASSWORD='your_password' psql -U nebula_admin -d nebula_db -f "$file"
    fi
done

echo "All migrations completed successfully!"
```

```bash
chmod +x run_migrations.sh
./run_migrations.sh
```

### Migration Verification

```bash
# Check migration history
psql -U nebula_admin -d nebula_db -c "SELECT * FROM public.migrations ORDER BY version;"

# Expected output:
#  version |      name       |     executed_at     
# ---------+-----------------+---------------------
#  001     | Initial schema  | 2024-01-15 10:30:00
```

---

## Seeding Data

### Run All Seeds

```bash
#!/bin/bash
# run_seeds.sh

set -e

echo "Seeding database..."

for file in database/seeds/*.sql; do
    if [ -f "$file" ]; then
        echo "Seeding: $file"
        PGPASSWORD='your_password' psql -U nebula_admin -d nebula_db -f "$file"
    fi
done

echo "All seeds completed successfully!"
```

```bash
chmod +x run_seeds.sh
./run_seeds.sh
```

### Verify Seed Data

```bash
# Check roles
psql -U nebula_admin -d nebula_db -c "SELECT * FROM public.roles;"

# Check permissions
psql -U nebula_admin -d nebula_db -c "SELECT * FROM public.permissions LIMIT 10;"

# Check settings
psql -U nebula_admin -d nebula_db -c "SELECT key, value FROM admin.settings LIMIT 10;"

# Check feature flags
psql -U nebula_admin -d nebula_db -c "SELECT name, is_enabled FROM admin.feature_flags;"
```

---

## Verification

### 1. Verify Schema

```bash
# List all schemas
psql -U nebula_admin -d nebula_db -c "\dn"

# Expected output:
#   List of schemas
#   Name     | Owner
# ----------+--------
#   admin    | nebula_admin
#   analytics| nebula_admin
#   audit    | nebula_admin
#   auth     | nebula_admin
#   notifications | nebula_admin
#   public   | nebula_admin
#   search   | nebula_admin
#   storage  | nebula_admin
```

### 2. Verify Tables

```bash
# List all tables
psql -U nebula_admin -d nebula_db -c "\dt *.*"

# Count tables per schema
psql -U nebula_admin -d nebula_db -c "
SELECT 
    schemaname,
    COUNT(*) as table_count
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
GROUP BY schemaname
ORDER BY schemaname;
"
```

### 3. Verify Indexes

```bash
# List all indexes
psql -U nebula_admin -d nebula_db -c "
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename;
"
```

### 4. Verify Functions

```bash
# List all functions
psql -U nebula_admin -d nebula_db -c "\df *.*"

# Test utility functions
psql -U nebula_admin -d nebula_db -c "SELECT update_updated_at_column();"
psql -U nebula_admin -d nebula_db -c "SELECT cleanup_expired_tokens();"
```

### 5. Verify Triggers

```bash
# List all triggers
psql -U nebula_admin -d nebula_db -c "
SELECT 
    schemaname,
    tablename,
    triggername,
    action_timing,
    event_manipulation
FROM pg_trigger
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename;
"
```

### 6. Verify Constraints

```bash
# List all constraints
psql -U nebula_admin -d nebula_db -c "
SELECT 
    conname as constraint_name,
    contype as constraint_type,
    conrelid::regclass as table_name
FROM pg_constraint
WHERE conrelid::regclass::schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY conrelid::regclass::schema, conrelid::regclass;
"
```

### 7. Test Database Connection

```bash
# Test connection as app user
psql -U nebula_app -d nebula_db -c "SELECT 1;"

# Expected output: ?column? 
#                  1
```

---

## Development Workflow

### 1. Create New Migration

```bash
# Create migration file
touch database/schema/002_add_new_feature.sql

# Edit migration file
nano database/schema/002_add_new_feature.sql
```

Example migration:

```sql
-- ============================================
-- Add New Feature
-- ============================================

-- Add new column
ALTER TABLE public.users 
    ADD COLUMN IF NOT EXISTS new_feature_enabled BOOLEAN DEFAULT FALSE;

-- Create index
CREATE INDEX IF NOT EXISTS idx_users_new_feature 
    ON public.users(new_feature_enabled) 
    WHERE is_deleted = FALSE;

-- Update migration tracking
INSERT INTO public.migrations (version, name) 
VALUES ('002', 'Add new feature')
ON CONFLICT (version) DO NOTHING;
```

### 2. Test Migration

```bash
# Test on development database
psql -U nebula_admin -d nebula_db_dev -f database/schema/002_add_new_feature.sql

# Verify changes
psql -U nebula_admin -d nebula_db_dev -c "\d public.users"
```

### 3. Rollback if Needed

```bash
# Create rollback script
nano database/schema/002_add_new_feature_rollback.sql
```

Example rollback:

```sql
-- ============================================
-- Rollback: Add New Feature
-- ============================================

-- Drop index
DROP INDEX IF EXISTS public.idx_users_new_feature;

-- Drop column
ALTER TABLE public.users 
    DROP COLUMN IF EXISTS new_feature_enabled;

-- Remove migration record
DELETE FROM public.migrations WHERE version = '002';
```

Run rollback:

```bash
psql -U nebula_admin -d nebula_db -f database/schema/002_add_new_feature_rollback.sql
```

### 4. Create Seed Data (if needed)

```bash
# Create seed file
nano database/seeds/005_new_feature_data.sql
```

Example seed:

```sql
-- ============================================
-- Seed Data: New Feature
-- ============================================

INSERT INTO admin.settings (key, value, value_type, description, is_public)
VALUES ('new_feature.enabled', 'true', 'boolean', 'Enable new feature', TRUE)
ON CONFLICT (key) DO NOTHING;

SELECT 'New feature data seeded successfully' AS status;
```

---

## Testing

### 1. Unit Tests

Create test file `tests/test_database.py`:

```python
import pytest
import psycopg2
from psycopg2.extras import RealDictCursor

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'nebula_db_test',
    'user': 'nebula_admin',
    'password': 'test_password'
}

@pytest.fixture
def db_connection():
    """Create database connection for testing"""
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    yield conn
    conn.close()

def test_users_table_exists(db_connection):
    """Test that users table exists"""
    cursor = db_connection.cursor()
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'users'
        );
    """)
    assert cursor.fetchone()[0] is True

def test_roles_seeded(db_connection):
    """Test that roles are seeded"""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM public.roles WHERE is_system = TRUE;")
    roles = cursor.fetchall()
    assert len(roles) == 5  # super_admin, admin, moderator, user, guest

def test_permissions_seeded(db_connection):
    """Test that permissions are seeded"""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT COUNT(*) FROM public.permissions;")
    count = cursor.fetchone()[0]
    assert count > 0

def test_settings_seeded(db_connection):
    """Test that settings are seeded"""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT COUNT(*) FROM admin.settings;")
    count = cursor.fetchone()[0]
    assert count > 0

def test_feature_flags_seeded(db_connection):
    """Test that feature flags are seeded"""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT COUNT(*) FROM admin.feature_flags;")
    count = cursor.fetchone()[0]
    assert count > 0
```

Run tests:

```bash
# Install pytest
pip install pytest psycopg2-binary

# Run tests
pytest tests/test_database.py -v
```

### 2. Integration Tests

```python
# tests/test_database_integration.py

def test_user_creation_workflow(db_connection):
    """Test complete user creation workflow"""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)
    
    # Create user
    cursor.execute("""
        INSERT INTO public.users (email, password_hash, email_verified)
        VALUES (%s, %s, %s)
        RETURNING id, email;
    """, ('test@example.com', 'hashed_password', True))
    
    user = cursor.fetchone()
    assert user['email'] == 'test@example.com'
    
    # Create profile
    cursor.execute("""
        INSERT INTO public.profiles (user_id, first_name, last_name)
        VALUES (%s, %s, %s)
        RETURNING *;
    """, (user['id'], 'Test', 'User'))
    
    profile = cursor.fetchone()
    assert profile['first_name'] == 'Test'
    
    # Assign role
    cursor.execute("""
        INSERT INTO public.user_roles (user_id, role_id)
        SELECT %s, id FROM public.roles WHERE name = 'user'
        RETURNING *;
    """, (user['id'],))
    
    user_role = cursor.fetchone()
    assert user_role is not None
    
    # Cleanup
    cursor.execute("DELETE FROM public.user_roles WHERE user_id = %s", (user['id'],))
    cursor.execute("DELETE FROM public.profiles WHERE user_id = %s", (user['id'],))
    cursor.execute("DELETE FROM public.users WHERE id = %s", (user['id'],))
```

### 3. Performance Tests

```python
# tests/test_database_performance.py
import time

def test_query_performance(db_connection):
    """Test query performance"""
    cursor = db_connection.cursor()
    
    # Test user lookup by email
    start = time.time()
    cursor.execute("SELECT * FROM public.users WHERE email = 'test@example.com';")
    cursor.fetchone()
    duration = time.time() - start
    
    assert duration < 0.1  # Should complete in < 100ms

def test_index_performance(db_connection):
    """Test index usage"""
    cursor = db_connection.cursor()
    
    # Check if index is used
    cursor.execute("""
        EXPLAIN ANALYZE
        SELECT * FROM public.users 
        WHERE email = 'test@example.com' AND is_deleted = FALSE;
    """)
    
    plan = cursor.fetchall()
    plan_text = ' '.join([str(row) for row in plan])
    
    # Verify index is used
    assert 'idx_users_email' in plan_text or 'idx_users_email_unique' in plan_text
```

---

## Deployment

### 1. Production Database Setup

```bash
# Create production database
sudo -u postgres createdb -O nebula_admin nebula_db_prod

# Create production user
sudo -u postgres psql -c "
    CREATE ROLE nebula_app_prod WITH 
        LOGIN 
        NOSUPERUSER 
        NOCREATEDB 
        NOCREATEROLE 
        PASSWORD 'production_secure_password';
"

# Grant minimal permissions
sudo -u postgres psql -d nebula_db_prod -c "
    GRANT CONNECT ON DATABASE nebula_db_prod TO nebula_app_prod;
    GRANT USAGE ON SCHEMA public, auth, search, analytics, notifications, storage, audit, admin TO nebula_app_prod;
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public, auth, search, analytics, notifications, storage, audit, admin TO nebula_app_prod;
    GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public, auth, search, analytics, notifications, storage, audit, admin TO nebula_app_prod;
"
```

### 2. Run Migrations on Production

```bash
# Backup first!
./scripts/backup.sh

# Run migrations
export DB_PASSWORD='production_secure_password'
python database/scripts/migrate.py

# Verify
psql -U nebula_admin -d nebula_db_prod -c "SELECT * FROM public.migrations;"
```

### 3. Configure Connection Pooling

Install PgBouncer:

```bash
# Ubuntu/Debian
sudo apt-get install pgbouncer

# macOS
brew install pgbouncer
```

Configure `/etc/pgbouncer/pgbouncer.ini`:

```ini
[databases]
nebula_db = host=localhost port=5432 dbname=nebula_db

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 10
reserve_pool_size = 5
max_db_connections = 50
max_user_connections = 25
server_lifetime = 3600
server_idle_timeout = 600
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1
```

Start PgBouncer:

```bash
sudo systemctl start pgbouncer
sudo systemctl enable pgbouncer
```

Update application configuration to use PgBouncer:

```python
# backend/app/config.py
DATABASE_URL = "postgresql://nebula_app:password@localhost:6432/nebula_db"
```

### 4. Configure Backups

Create backup script `database/scripts/backup.sh`:

```bash
#!/bin/bash
# Database backup script

set -e

BACKUP_DIR="/backups/nebula_db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/nebula_db_$TIMESTAMP.dump"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
echo "Creating backup: $BACKUP_FILE"
pg_dump -U nebula_admin -d nebula_db -Fc -f $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.dump.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

Make executable:

```bash
chmod +x database/scripts/backup.sh
```

Schedule with cron:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/nebula-search-engine/database/scripts/backup.sh
```

### 5. Configure Monitoring

```sql
-- Create monitoring views
CREATE OR REPLACE VIEW admin.database_stats AS
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows
FROM pg_stat_user_tables
ORDER BY schemaname, tablename;

-- Create connection stats view
CREATE OR REPLACE VIEW admin.connection_stats AS
SELECT 
    state,
    COUNT(*) as count,
    MAX(now() - state_change) as max_duration
FROM pg_stat_activity
WHERE datname = 'nebula_db'
GROUP BY state;

-- Create slow query view
CREATE OR REPLACE VIEW admin.slow_queries AS
SELECT 
    query,
    calls,
    mean_exec_time,
    total_exec_time,
    rows
FROM pg_stat_statements
WHERE dbid = (SELECT oid FROM pg_database WHERE datname = 'nebula_db')
ORDER BY mean_exec_time DESC
LIMIT 100;
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Refused

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check port is listening
sudo netstat -tlnp | grep 5432

# Check pg_hba.conf
sudo cat /etc/postgresql/15/main/pg_hba.conf
```

#### 2. Permission Denied

```bash
# Grant permissions
sudo -u postgres psql -d nebula_db -c "
    GRANT ALL ON SCHEMA public TO nebula_app;
    GRANT ALL ON ALL TABLES IN SCHEMA public TO nebula_app;
    GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO nebula_app;
"
```

#### 3. Extension Not Found

```bash
# Install extension
sudo -u postgres psql -d nebula_db -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"

# If fails, install postgresql-contrib
sudo apt-get install postgresql-contrib-15
```

#### 4. Migration Failed

```bash
# Check migration status
psql -U nebula_admin -d nebula_db -c "SELECT * FROM public.migrations;"

# Rollback last migration
psql -U nebula_admin -d nebula_db -f database/schema/001_initial_schema_rollback.sql

# Re-run migration
psql -U nebula_admin -d nebula_db -f database/schema/001_initial_schema.sql
```

#### 5. Slow Queries

```bash
# Enable query logging
sudo -u postgres psql -c "ALTER SYSTEM SET log_min_duration_statement = 1000;"
sudo systemctl restart postgresql

# Check slow queries
psql -U nebula_admin -d nebula_db -c "SELECT * FROM admin.slow_queries LIMIT 10;"

# Analyze table
psql -U nebula_admin -d nebula_db -c "ANALYZE public.users;"
```

### Debug Mode

```bash
# Enable verbose logging
sudo -u postgres psql -c "
    ALTER SYSTEM SET log_statement = 'all';
    ALTER SYSTEM SET log_duration = on;
    ALTER SYSTEM SET log_line_prefix = '%t [%p-%l] %q%u@%d ';
"

# Restart PostgreSQL
sudo systemctl restart postgresql

# Check logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

---

## Best Practices

### 1. Migration Best Practices

- ✅ **Always test migrations** on development before production
- ✅ **Create rollback scripts** for every migration
- ✅ **Use transactions** for complex migrations
- ✅ **Backup before migrating** production database
- ✅ **Never modify existing migrations** - create new ones
- ✅ **Use IF NOT EXISTS/IF EXISTS** for idempotency
- ✅ **Document complex changes** with comments

### 2. Performance Best Practices

- ✅ **Use indexes** on frequently queried columns
- ✅ **Use partial indexes** for soft delete filtering
- ✅ **Use composite indexes** for common query patterns
- ✅ **Use GIN indexes** for JSONB and full-text search
- ✅ **Regularly ANALYZE tables** for query optimizer
- ✅ **Monitor slow queries** and optimize them
- ✅ **Use connection pooling** (PgBouncer)

### 3. Security Best Practices

- ✅ **Use strong passwords** for database users
- ✅ **Grant minimal permissions** to application user
- ✅ **Enable SSL/TLS** for connections
- ✅ **Use parameterized queries** to prevent SQL injection
- ✅ **Enable audit logging** for sensitive operations
- ✅ **Regular security updates** for PostgreSQL
- ✅ **Encrypt sensitive data** using pgcrypto

### 4. Maintenance Best Practices

- ✅ **Regular backups** (daily minimum)
- ✅ **Monitor disk usage** and storage growth
- ✅ **Clean up old data** according to retention policies
- ✅ **Update statistics** regularly (ANALYZE)
- ✅ **Vacuum tables** to prevent bloat
- ✅ **Monitor replication lag** (if using replicas)
- ✅ **Test restore procedures** regularly

### 5. Development Best Practices

- ✅ **Use separate databases** for dev, staging, prod
- ✅ **Version control** all migrations and seeds
- ✅ **Code review** for database changes
- ✅ **Document schema changes** in commit messages
- ✅ **Use ORM** (SQLAlchemy) for application code
- ✅ **Write database tests** for critical operations
- ✅ **Use database transactions** for data consistency

---

## Useful Commands

### Database Information

```bash
# Database size
psql -U nebula_admin -d nebula_db -c "SELECT pg_size_pretty(pg_database_size('nebula_db'));"

# Table sizes
psql -U nebula_admin -d nebula_db -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# Index sizes
psql -U nebula_admin -d nebula_db -c "
SELECT 
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
"
```

### Database Maintenance

```bash
# Vacuum all tables
psql -U nebula_admin -d nebula_db -c "VACUUM VERBOSE;"

# Analyze all tables
psql -U nebula_admin -d nebula_db -c "ANALYZE;"

# Reindex database
psql -U nebula_admin -d nebula_db -c "REINDEX DATABASE nebula_db;"

# Check for bloat
psql -U nebula_admin -d nebula_db -c "
SELECT 
    schemaname,
    tablename,
    n_dead_tup,
    last_autovacuum
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
ORDER BY n_dead_tup DESC;
"
```

### User Management

```bash
# List all users
psql -U nebula_admin -d nebula_db -c "\du"

# Create new user
sudo -u postgres psql -c "CREATE ROLE new_user WITH LOGIN PASSWORD 'password';"

# Grant permissions
sudo -u postgres psql -d nebula_db -c "GRANT SELECT ON ALL TABLES IN SCHEMA public TO new_user;"

# Change password
sudo -u postgres psql -c "ALTER USER nebula_app WITH PASSWORD 'new_password';"

# Drop user
sudo -u postgres psql -c "DROP ROLE new_user;"
```

---

## Next Steps

1. ✅ Database schema created
2. ✅ Migrations and seeds configured
3. ✅ Development environment set up
4. ⬜ Create ORM models (SQLAlchemy)
5. ⬜ Implement database repositories
6. ⬜ Write comprehensive tests
7. ⬜ Set up CI/CD pipeline
8. ⬜ Deploy to staging
9. ⬜ Load testing and optimization
10. ⬜ Deploy to production

---

## Support

For issues or questions:

- **Documentation**: See `docs/DATABASE_ARCHITECTURE.md`
- **ERD**: See `docs/DATABASE_ERD.md`
- **Issues**: Create issue in GitHub repository
- **Team**: Contact database team

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Status**: Production-Ready