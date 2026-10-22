# Nebula Search Engine - Authentication System Deployment Guide

## Prerequisites

- Python 3.9+
- PostgreSQL 12+ (recommended) or SQLite
- Redis (optional, for distributed cache)
- SMTP server (for email verification and password reset)

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Additional Dependencies for Authentication

```bash
pip install pyotp qrcode[pil] httpx
```

### 3. Environment Configuration

Create `.env` file in the backend directory:

```env
# Database
DATABASE_URL=postgresql://nebula:nebula@localhost:5432/nebula
# OR for SQLite:
# DATABASE_URL=nebula.db

# JWT Configuration (CRITICAL: Use strong secret in production)
JWT_SECRET=your-very-long-and-random-secret-key-here-at-least-32-characters
JWT_EXPIRY_MINUTES=30
JWT_ISSUER=nebula-search
JWT_AUDIENCE=nebula-api

# Refresh Tokens
REFRESH_TOKEN_DAYS=7

# Cookie Configuration
AUTH_COOKIE_MODE=true
COOKIE_SECURE=true
COOKIE_SAMESITE=lax

# Brute Force Protection
MAX_LOGIN_ATTEMPTS=5
LOGIN_LOCKOUT_MINUTES=15

# Rate Limiting
SIGNUP_RATE_LIMIT=5
LOGIN_RATE_LIMIT=5
REFRESH_RATE_LIMIT=10

# Email Verification
REQUIRE_EMAIL_VERIFICATION=false
EMAIL_VERIFICATION_EXPIRY_HOURS=24

# Password Reset
PASSWORD_RESET_EXPIRY_HOURS=1

# MFA (Optional)
ENABLE_MFA=false
MFA_ISSUER=Nebula Search

# OAuth (Optional)
ENABLE_OAUTH=false
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
APPLE_CLIENT_ID=
APPLE_CLIENT_SECRET=

# Email Service (Required for verification and password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@nebula-search.io
SMTP_FROM_NAME=Nebula Search
SMTP_USE_TLS=true

# Redis (Optional - for distributed cache)
REDIS_URL=redis://localhost:6379/0

# Application
APP_ENV=production
CORS_ORIGINS=https://nebula-search.io,https://app.nebula-search.io
RATE_LIMIT_PER_MINUTE=60

# Audit Logging
ENABLE_AUDIT_LOGS=true
```

### 4. Database Migration

Run database migrations to create authentication tables:

```bash
# For PostgreSQL
psql -U nebula -d nebula -f database/schema/001_initial_schema.sql

# For SQLite (automatic on first run)
python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 5. Verify Database Tables

Ensure these tables exist:

**Required:**
- `public.users` - User accounts
- `auth.sessions` - Refresh token sessions
- `auth.email_verification` - Email verification tokens
- `auth.password_reset` - Password reset tokens
- `audit_logs` - Audit logging

**Optional (for OAuth):**
- `auth.oauth_accounts` - OAuth account linking

**Optional (for MFA):**
- MFA fields in `users` table (mfa_enabled, mfa_secret, mfa_backup_codes)

## Deployment

### Development

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

#### Using Gunicorn with Uvicorn Workers

```bash
cd backend
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Using Docker

```bash
# Build image
docker build -t nebula-backend -f docker/Dockerfile .

# Run container
docker run -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/storage:/app/storage \
  nebula-backend
```

#### Using Docker Compose

```bash
docker-compose up -d backend
```

## Security Checklist

### Pre-Production

- [ ] **JWT_SECRET**: Set strong, random secret (minimum 32 characters)
- [ ] **HTTPS**: Enable HTTPS in production
- [ ] **COOKIE_SECURE**: Set to `true` in production
- [ ] **Email Service**: Configure SMTP settings
- [ ] **Rate Limiting**: Enable and configure rate limits
- [ ] **Audit Logging**: Enable audit logging
- [ ] **Database**: Use PostgreSQL for production
- [ ] **Redis**: Configure Redis for distributed cache (optional but recommended)
- [ ] **CORS**: Configure allowed origins
- [ ] **Firewall**: Restrict database access
- [ ] **Secrets Management**: Use environment variables or secret management service

### Post-Deployment

- [ ] **Test Registration**: Verify email verification flow
- [ ] **Test Login**: Verify authentication works
- [ ] **Test Password Reset**: Verify email delivery
- [ ] **Test MFA**: Verify MFA setup and login (if enabled)
- [ ] **Test OAuth**: Verify OAuth providers (if enabled)
- [ ] **Monitor Logs**: Check audit logs for errors
- [ ] **Rate Limits**: Verify rate limiting is working
- [ ] **Session Management**: Test session termination
- [ ] **Security Headers**: Verify security headers are present

## Configuration Options

### Email Verification

To require email verification:

```env
REQUIRE_EMAIL_VERIFICATION=true
```

Users will not be able to access protected features until they verify their email.

### Multi-Factor Authentication

To enable MFA:

```env
ENABLE_MFA=true
```

MFA is optional for users unless enforced by application logic.

### OAuth Integration

To enable OAuth:

```env
ENABLE_OAUTH=true
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

Configure OAuth apps in provider consoles:
- **Google**: https://console.cloud.google.com/apis/credentials
- **GitHub**: https://github.com/settings/developers
- **Microsoft**: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps
- **Apple**: https://developer.apple.com/account/resources/identifiers/list

## Monitoring

### Audit Logs

Monitor audit logs for security events:

```python
# Get recent security events
from app.database.repositories.audit import AuditRepository
from app.database import get_db

async def get_security_events():
    db = await get_db()
    audit = AuditRepository(db)
    events = await audit.get_security_events(limit=100)
    return events
```

### Key Metrics to Monitor

1. **Failed Login Attempts**: Spike may indicate brute force attack
2. **Account Lockouts**: Frequent lockouts may indicate attack
3. **Password Reset Requests**: Unusual volume may indicate abuse
4. **MFA Enrollment**: Track MFA adoption rate
5. **Token Refresh Rate**: Monitor for unusual patterns
6. **Session Terminations**: Track suspicious activity

### Log Analysis

```bash
# View recent audit logs
tail -f logs/nebula.log | grep "audit"

# Count failed logins in last hour
grep "failed_login" logs/nebula.log | awk -v cutoff=$(date -d '1 hour ago' '+%Y-%m-%dT%H:%M') '$0 ~ cutoff' | wc -l
```

## Troubleshooting

### Email Not Sending

1. Check SMTP credentials
2. Verify SMTP host and port
3. Check firewall rules
4. Review email service logs
5. Test with `python -c "from app.services.email import email_service; import asyncio; print(asyncio.run(email_service.send_email('test@example.com', 'Test', 'Test')))"`

### JWT Token Errors

1. Verify JWT_SECRET is set
2. Check token expiration times
3. Verify system clock is synchronized
4. Check audience and issuer claims

### Rate Limiting Issues

1. Verify Redis is running (if using Redis)
2. Check rate limit configuration
3. Monitor memory usage (in-memory fallback)
4. Review rate limit logs

### Database Connection Issues

1. Verify DATABASE_URL is correct
2. Check database server is running
3. Verify credentials
4. Check connection pool settings

## Performance Tuning

### Database

1. **Indexes**: Ensure indexes on frequently queried columns
2. **Connection Pooling**: Configure connection pool size
3. **Query Optimization**: Monitor slow queries
4. **Partitioning**: Partition audit_logs by date (for large datasets)

### Cache

1. **Redis**: Use Redis for distributed cache
2. **TTL**: Set appropriate TTL values
3. **Memory**: Monitor cache memory usage
4. **Eviction**: Configure eviction policy

### Rate Limiting

1. **Redis**: Use Redis for distributed rate limiting
2. **In-Memory**: Fallback to in-memory for single instance
3. **Monitoring**: Track rate limit hits

## Backup and Recovery

### Database Backup

```bash
# PostgreSQL
pg_dump -U nebula -d nebula > backup.sql

# SQLite
cp nebula.db backup.db
```

### Restore

```bash
# PostgreSQL
psql -U nebula -d nebula < backup.sql

# SQLite
cp backup.db nebula.db
```

## Scaling

### Horizontal Scaling

1. **Load Balancer**: Use load balancer (nginx, AWS ALB, etc.)
2. **Session Storage**: Use Redis for shared session storage
3. **Database**: Use PostgreSQL with read replicas
4. **Cache**: Use Redis cluster for distributed cache

### Vertical Scaling

1. **Workers**: Increase Gunicorn workers
2. **Database**: Upgrade database instance
3. **Cache**: Increase Redis memory

## Security Hardening

### Production Security

1. **HTTPS Only**: Disable HTTP
2. **Strong Secrets**: Use cryptographically random secrets
3. **Firewall**: Restrict database and Redis access
4. **VPN**: Consider VPN for admin access
5. **Monitoring**: Set up security monitoring
6. **Alerts**: Configure alerts for security events
7. **Regular Updates**: Keep dependencies updated
8. **Penetration Testing**: Regular security audits

### Compliance

- **GDPR**: User data export and deletion implemented
- **SOC 2**: Audit logging and access controls in place
- **OWASP**: Follows OWASP Top 10 guidelines

## Support

For deployment issues:
- Documentation: https://docs.nebula-search.io
- GitHub Issues: https://github.com/Sky-254-1/Nebula-search-engine-/issues
- Email: support@nebula-search.io