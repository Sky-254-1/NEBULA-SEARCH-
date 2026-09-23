# Database Migrations

This directory contains all database migration files for the IOIS (Nebula) application.

## Migration Naming Convention

Migrations follow the format: `{version}_{description}.sql`

- Version: 3-digit zero-padded number (001, 002, etc.)
- Description: Short description of the migration
- Example: `001_initial_schema.sql`, `002_add_user_preferences.sql`

## Migration Order

1. **001_initial_schema.sql** - Complete initial schema with all tables, indexes, triggers, and seed data
2. **002_add_user_preferences.sql** - Additional user preference fields
3. **003_add_file_versioning.sql** - File versioning enhancements
4. **004_add_analytics.sql** - Analytics schema
5. **005_add_notifications.sql** - Notifications schema
6. **006_add_audit.sql** - Audit logging
7. **007_add_admin.sql** - Admin system
8. **008_enable_rls.sql** - Row-level security
9. **009_add_partitioning.sql** - Table partitioning
10. **010_add_materialized_views.sql** - Analytics views

## Running Migrations

### Using psql

```bash
# Run single migration
psql -U nebula_admin -d nebula_db -f database/migrations/001_initial_schema.sql

# Run all migrations in order
for file in database/migrations/*.sql; do
    echo "Running $file..."
    psql -U nebula_admin -d nebula_db -f "$file"
done
```

### Using Python Script

```bash
# Run migration script
python database/scripts/migrate.py
```

### Using Docker

```bash
# Run migrations in Docker container
docker-compose exec db psql -U nebula_admin -d nebula_db -f /migrations/001_initial_schema.sql
```

## Migration Best Practices

1. **Never modify existing migrations** - Create new migration files for changes
2. **Test migrations** - Always test on staging before production
3. **Backup before migrating** - Create database backup before running migrations
4. **Use transactions** - Wrap migrations in transactions when possible
5. **Idempotent scripts** - Use `IF NOT EXISTS` and `IF EXISTS` clauses
6. **Document changes** - Add comments explaining complex changes

## Rollback Strategy

Each migration should have a corresponding rollback script:

```
database/migrations/
├── 001_initial_schema.sql
├── 001_initial_schema_rollback.sql
├── 002_add_user_preferences.sql
├── 002_add_user_preferences_rollback.sql
└── ...
```

### Rollback Example

```sql
-- 001_initial_schema_rollback.sql
DROP SCHEMA IF EXISTS admin CASCADE;
DROP SCHEMA IF EXISTS audit CASCADE;
DROP SCHEMA IF EXISTS storage CASCADE;
DROP SCHEMA IF EXISTS notifications CASCADE;
DROP SCHEMA IF EXISTS analytics CASCADE;
DROP SCHEMA IF EXISTS search CASCADE;
DROP SCHEMA IF EXISTS auth CASCADE;
DROP TABLE IF EXISTS public.migrations CASCADE;
```

## Migration Tracking

Migrations are tracked in the `public.migrations` table:

```sql
SELECT * FROM public.migrations ORDER BY version;
```

## Creating New Migrations

1. Create new SQL file with next version number
2. Include schema changes, indexes, and seed data
3. Test migration on development database
4. Create corresponding rollback script
5. Update this README with migration description
6. Commit migration files to version control

## Migration Checklist

- [ ] Migration file created with correct naming
- [ ] Schema changes tested on development
- [ ] Rollback script created
- [ ] Seed data included (if needed)
- [ ] Indexes optimized
- [ ] Documentation updated
- [ ] Team notified of changes
- [ ] Staging deployment tested
- [ ] Production deployment scheduled