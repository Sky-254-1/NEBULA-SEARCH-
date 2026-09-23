# Database Seed Data

This directory contains seed data files for populating the database with initial data.

## Seed Files

### 001_roles.sql
Seeds the RBAC roles:
- super_admin
- admin
- moderator
- user
- guest

### 002_permissions.sql
Seeds granular permissions for all resources:
- User management permissions
- Search permissions
- File management permissions
- Analytics permissions
- Admin permissions

### 003_settings.sql
Seeds application configuration settings:
- App metadata
- Authentication settings
- Search configuration
- Storage limits
- Analytics retention
- Notification settings

### 004_feature_flags.sql
Seeds feature flags for gradual rollout:
- Vector search
- AI synthesis
- Advanced analytics
- File versioning
- Multi-tenant support
- API access

## Running Seeds

### Using psql

```bash
# Run all seed files in order
for file in database/seeds/*.sql; do
    echo "Seeding $file..."
    psql -U nebula_admin -d nebula_db -f "$file"
done
```

### Using Python Script

```bash
# Run seed script
python database/scripts/seed.py
```

### Using Docker

```bash
# Run seeds in Docker container
docker-compose exec db psql -U nebula_admin -d nebula_db -f /seeds/001_roles.sql
```

## Seed Data Guidelines

1. **Idempotent** - Seeds should be safe to run multiple times
2. **Ordered** - Respect foreign key dependencies
3. **Documented** - Include comments explaining data
4. **Minimal** - Only essential data, not test data
5. **Reversible** - Can be cleared and re-seeded

## Clearing Seed Data

```sql
-- Clear all seed data (be careful!)
TRUNCATE TABLE admin.feature_flags CASCADE;
TRUNCATE TABLE admin.settings CASCADE;
TRUNCATE TABLE public.role_permissions CASCADE;
TRUNCATE TABLE public.permissions CASCADE;
TRUNCATE TABLE public.user_roles CASCADE;
TRUNCATE TABLE public.roles CASCADE;
```

## Adding New Seed Data

1. Create new SQL file with next version number
2. Use INSERT ... ON CONFLICT DO NOTHING for idempotency
3. Test seed on clean database
4. Update this README
5. Commit to version control

## Seed Checklist

- [ ] Seed file created with correct naming
- [ ] Data tested on clean database
- [ ] Foreign key dependencies respected
- [ ] Idempotent (safe to re-run)
- [ ] Documentation updated
- [ ] Team notified of changes