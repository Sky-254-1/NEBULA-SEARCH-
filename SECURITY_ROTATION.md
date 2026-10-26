# Credential Rotation Guide

This document provides comprehensive procedures for rotating all credentials used in the Nebula Search application.

## Table of Contents

1. [When to Rotate Credentials](#when-to-rotate-credentials)
2. [General Rotation Guidelines](#general-rotation-guidelines)
3. [Credential-Specific Rotation Procedures](#credential-specific-rotation-procedures)
4. [Verifying Rotation Success](#verifying-rotation-success)
5. [Multi-Service Rotation Scenarios](#multi-service-rotation-scenarios)
6. [Emergency Response Procedures](#emergency-response-procedures)
7. [Automation Suggestions](#automation-suggestions)

---

## When to Rotate Credentials

### Mandatory Rotation Triggers

| Trigger | Action Required |
|---------|----------------|
| **Security Breach** | Immediately rotate all potentially exposed credentials |
| **Employee Departure** | Rotate credentials the departing employee had access to |
| **Credential Suspected Compromise** | Rotate immediately, even without confirmation |
| **Periodic Review Cycle** | Execute scheduled rotation per organization policy (recommended: quarterly) |
| **Audit Finding** | Rotate as specified in remediation plan |

### Recommended Rotation Schedule

| Credential Type | Rotation Frequency | Notes |
|----------------|-------------------|-------|
| Database Passwords | Quarterly | Include rotation in maintenance windows |
| JWT Secrets | Quarterly | Requires coordinated deployment |
| Session Secrets | Quarterly | Invalidates active sessions |
| Encryption Keys | Annually | Requires data migration |
| API Keys | Quarterly | Align with provider policies |
| OAuth Secrets | Quarterly | Provider-specific policies may vary |
| MinIO Credentials | Quarterly | Align with storage team policies |
| SMTP Credentials | Annually | If used for production email |
| Grafana Passwords | Monthly | Compliance requirement |

---

## General Rotation Guidelines

### Before Rotation

1. **Backup Configuration**: Ensure you have current configuration backups
2. **Coordinate Downtime**: Schedule during maintenance windows when possible
3. **Prepare New Credentials**: Generate new credentials before removing old ones
4. **Test Environment**: Verify new credentials work in staging first
5. **Notify Stakeholders**: Alert teams about potential service disruption
6. **Document Changes**: Log all changes in change management system

### During Rotation

1. **Generate New Credentials**: Use secure generation commands
2. **Update All Locations**: Update credentials in all places where they're stored
3. **Deploy Configuration**: Push updated configuration to services
4. **Restart Services**: Restart affected services in dependency order
5. **Verify Functionality**: Test each service individually

### After Rotation

1. **Verify All Services**: Confirm all services can authenticate
2. **Monitor Logs**: Watch for authentication failures in logs
3. **Validate Data Access**: Ensure data is accessible with new credentials
4. **Update Documentation**: Update any internal documentation
5. **Close Incident**: If emergency rotation, document the incident

### Security Best Practices

- **Never Commit Secrets**: All credentials should be in environment variables or secret management systems
- **Use Environment-Specific Secrets**: Development, staging, and production should use different credentials
- **Principle of Least Privilege**: Each credential should have minimal necessary permissions
- **Rotation Logging**: Log rotation events for audit purposes
- **Credential Expiration**: Set expiration dates where possible

---

## Credential-Specific Rotation Procedures

### Database Passwords (PostgreSQL)

#### Secure Generation

```bash
# Generate strong password (32 characters)
openssl rand -base64 32 | tr -d '\n' && echo

# Alternative: Hex format (64 characters)
openssl rand -hex 32

# Fallback using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Where to Update

| Location | Update Method |
|----------|--------------|
| PostgreSQL Database | `ALTER USER username WITH PASSWORD 'new_password';` |
| `.env.development` | Update `DATABASE_URL` or `POSTGRES_PASSWORD` |
| `.env.production` | Update `DATABASE_URL` or `POSTGRES_PASSWORD` |
| Kubernetes Secrets | `kubectl create secret generic db-credentials --from-literal=password=new_password -n nebula` |
| Docker Compose | Update `POSTGRES_PASSWORD` in `docker-compose.yml` |
| Cloud Provider | AWS RDS: Modify instance, DigitalOcean: Reset password in dashboard |

#### Services Need Restart

| Service | Restart Required | Command |
|---------|-----------------|---------|
| Backend API | Yes | `docker-compose restart backend` |
| Background Workers | Yes | `docker-compose restart indexer` |
| Frontend | No (server-side only) | N/A |

#### Migration Steps

1. Generate new password using secure generation command
2. Update PostgreSQL user password:
   ```sql
   ALTER USER nebula WITH PASSWORD 'new_secure_password';
   ```
3. Update `.env.production` with new password in DATABASE_URL
4. Update Kubernetes secret (if applicable):
   ```bash
   kubectl create secret generic nebula-db-credentials \
     --from-literal=password='new_secure_password' \
     --from-literal=username=nebula \
     -n nebula
   ```
5. Restart backend services:
   ```bash
   docker-compose restart backend indexer
   ```
6. Verify database connectivity:
   ```bash
   docker-compose exec backend python -c "import os, psycopg2; psycopg2.connect(os.getenv('DATABASE_URL'))"
   ```

---

### JWT Secrets

#### Secure Generation

```bash
# Generate 64-character hex secret
openssl rand -hex 32

# Fallback using Python (guarantees alphanumeric)
python -c "import secrets; print(secrets.token_hex(32))"
```

#### Where to Update

| Location | Update Method |
|----------|--------------|
| `.env.development` | Update `JWT_SECRET` |
| `.env.production` | Update `JWT_SECRET` |
| Kubernetes Secrets | `kubectl create secret generic app-secrets --from-literal=jwt-secret=new_secret -n nebula` |
| Docker Compose | Update `JWT_SECRET` in `docker-compose.yml` |
| Cloud Environment Variables | Update in platform dashboard |

#### Services Need Restart

| Service | Restart Required | Command |
|---------|-----------------|---------|
| Backend API | Yes | All tokens will be invalidated |
| Authentication Services | Yes | Login required for all users |

#### Migration Steps

1. Generate new JWT secret:
   ```bash
   JWT_SECRET=$(openssl rand -hex 32)
   echo "New JWT_SECRET: $JWT_SECRET"
   ```
2. Update `.env.production`:
   ```bash
   echo "JWT_SECRET=$JWT_SECRET" >> .env.production
   ```
3. Update Kubernetes secret (if applicable):
   ```bash
   kubectl create secret generic app-secrets \
     --from-literal=jwt-secret="$JWT_SECRET" \
     --from-literal=session-secret="$SESSION_SECRET" \
     --from-literal=encryption-key="$ENCRYPTION_KEY" \
     -n nebula
   ```
4. Update all environment files with new secret
5. Restart backend services:
   ```bash
   docker-compose restart backend
   # Or if using kubernetes
   kubectl rollout restart deployment/backend -n nebula
   ```
6. All active sessions will be invalidated - users must log in again
7. Verify authentication works with new tokens

**Important**: JWT secret rotation invalidates all existing tokens. Schedule during maintenance windows and notify users.

---

### Session Secrets

#### Secure Generation

```bash
# Generate 32-character base64 secret
openssl rand -base64 32 | tr -d '\n' && echo

# Fallback using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Where to Update

| Location | Update Method |
|----------|--------------|
| `.env.development` | Update `SESSION_SECRET` |
| `.env.production` | Update `SESSION_SECRET` |
| Kubernetes Secrets | Update in `app-secrets` |
| Docker Compose | Update `SESSION_SECRET` in `docker-compose.yml` |

#### Services Need Restart

| Service | Restart Required | Command |
|---------|-----------------|---------|
| Backend API | Yes | `docker-compose restart backend` |
| Redis (if used for sessions) | No | N/A |

#### Migration Steps

1. Generate new session secret:
   ```bash
   SESSION_SECRET=$(openssl rand -base64 32 | tr -d '\n')
   echo "New SESSION_SECRET: $SESSION_SECRET"
   ```
2. Update `.env.production`:
   ```bash
   echo "SESSION_SECRET=$SESSION_SECRET" >> .env.production
   ```
3. Update all environment files with new secret
4. Restart backend services:
   ```bash
   docker-compose restart backend
   ```
5. All active sessions will be invalidated
6. Verify session-based authentication works

**Note**: Session secret rotation will log out all active users.

---

### Encryption Keys

#### Secure Generation

```bash
# Generate 32-byte base64 encoded key (for AES-256)
openssl rand -base64 32 | tr -d '\n' && echo

# Fallback using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Where to Update

| Location | Update Method |
|----------|--------------|
| `.env.development` | Update `ENCRYPTION_KEY` |
| `.env.production` | Update `ENCRYPTION_KEY` |
| Kubernetes Secrets | Update in `app-secrets` |
| Docker Compose | Update `ENCRYPTION_KEY` in `docker-compose.yml` |

#### Services Need Restart

| Service | Restart Required | Command |
|---------|-----------------|---------|
| Backend API | Yes | `docker-compose restart backend` |

#### Migration Steps

1. Generate new encryption key:
   ```bash
   ENCRYPTION_KEY=$(openssl rand -base64 32 | tr -d '\n')
   echo "New ENCRYPTION_KEY: $ENCRYPTION_KEY"
   ```
2. Update `.env.production`:
   ```bash
   echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" >> .env.production
   ```
3. Verify key length (must be exactly 32 bytes after decoding):
   ```bash
   python -c "import base64; print(len(base64.b64decode('$ENCRYPTION_KEY')))"
   ```
4. Restart backend services:
   ```bash
   docker-compose restart backend
   ```
5. Test data encryption/decryption:
   ```bash
   docker-compose exec backend python -c "
   from app.services.encryption import EncryptionService
   enc = EncryptionService()
   encrypted = enc.encrypt('test')
   decrypted = enc.decrypt(encrypted)
   print(f'Original: test')
   print(f'Decrypted: {decrypted}')
   assert decrypted == 'test'
   print('Encryption working correctly')
   "
   ```

**Important**: Encryption key rotation requires migrating existing encrypted data using the old key.

---

### API Keys (OpenAI, Brave, SerpAPI)

#### Secure Generation

API keys are generated by the respective providers. Never generate them locally.

#### Where to Update

| Provider | Update Location |
|----------|----------------|
| OpenAI | [OpenAI Dashboard](https://platform.openai.com/api-keys) |
| Brave | [Brave Search API](https://brave.com/search-api/) |
| SerpAPI | [SerpAPI Dashboard](https://serpapi.com/manage-api-key) |

#### Services Need Restart

| Service | Restart Required | Command |
|---------|-----------------|---------|
| Backend API | Yes (to reload config) | `docker-compose restart backend` |

#### Migration Steps

1. Log in to provider dashboard
2. Navigate to API keys section
3. Create new API key
4. Copy the new key
5. Update `.env.production`:
   ```bash
   echo "OPENAI_API_KEY=your-new-key" >> .env.production
   echo "BRAVE_API_KEY=your-new-key" >> .env.production
   echo "SERPAPI_KEY=your-new-key" >> .env.production
   ```
6. Revoke old API keys in provider dashboard
7. Restart backend services:
   ```bash
   docker-compose restart backend
   ```
8. Test API connectivity:
   ```bash
   docker-compose exec backend python -c "
   from app.services.research import ResearchService
   import os
   service = ResearchService()
   # This will fail if API key is invalid
   print('Research service initialized with new key')
   "
   ```

**Important**: Always revoke old API keys after confirming new keys work.

---

### OAuth Secrets (Google, GitHub)

#### Secure Generation

OAuth credentials are generated by the respective providers. Never generate them locally.

#### Where to Update

| Provider | Update Location |
|----------|----------------|
| Google | [Google Cloud Console](https://console.cloud.google.com/apis/credentials) |
| GitHub | [GitHub Developer Settings](https://github.com/settings/developers) |

#### Services Need Restart

| Service | Restart Required | Command |
|---------|-----------------|---------|
| Backend API | Yes | `docker-compose restart backend` |

#### Migration Steps for Google OAuth

1. Log in to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **APIs & Services** → **Credentials**
3. Click **Create Credentials** → **OAuth client ID**
4. Configure consent screen if prompted
5. Select **Web application**
6. Add authorized origins:
   - `http://localhost:8000` (development)
   - Your production domain
7. Add authorized redirect URIs:
   - `http://localhost:8000/api/v1/auth/oauth2/callback/google` (development)
   - Your production callback URL
8. Copy the **Client ID** and **Client Secret**
9. Update `.env.production`:
   ```bash
   echo "GOOGLE_OAUTH2_CLIENT_ID=your-client-id" >> .env.production
   echo "GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret" >> .env.production
   ```
10. Restart backend:
    ```bash
    docker-compose restart backend
    ```

#### Migration Steps for GitHub OAuth

1. Log in to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click **OAuth Apps** → **New OAuth App**
3. Fill in application details
4. Set **Authorization callback URL**:
   - `http://localhost:8000/api/v1/auth/oauth2/callback/github` (development)
   - Your production callback URL
5. Click **Register application**
6. Copy the **Client ID** and generate **Client Secret**
7. Update `.env.production`:
   ```bash
   echo "GITHUB_OAUTH2_CLIENT_ID=your-client-id" >> .env.production
   echo "GITHUB_OAUTH2_CLIENT_SECRET=your-client-secret" >> .env.production
   ```
8. Restart backend:
   ```bash
   docker-compose restart backend
   ```

**Important**: Update redirect URIs in both development and production environments.

---

### MinIO Credentials

#### Secure Generation

```bash
# Access Key (20 characters, alphanumeric)
openssl rand -base64 20 | tr -d '\n' | head -c 20 && echo

# Secret Key (40 characters, alphanumeric + symbols)
openssl rand -base64 60 | tr -d '\n' | head -c 40 && echo
```

#### Where to Update

| Location | Update Method |
|----------|--------------|
| `.env.development` | Update `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` |
| `.env.production` | Update `MINIO_ROOT_USER` and `MINIO_ROOT_PASSWORD` |
| MinIO Console | MinIO dashboard → Access Keys |
| Docker Compose | Update in `docker-compose.yml` |

#### Services Need Restart

| Service | Restart Required | Command |
|---------|-----------------|---------|
| Backend API | Yes | `docker-compose restart backend` |
| MinIO | Yes | `docker-compose restart minio` |

#### Migration Steps

1. Generate new credentials:
   ```bash
   MINIO_ACCESS_KEY=$(openssl rand -base64 20 | tr -d '\n' | head -c 20)
   MINIO_SECRET_KEY=$(openssl rand -base64 60 | tr -d '\n' | head -c 40)
   echo "New MINIO_ACCESS_KEY: $MINIO_ACCESS_KEY"
   echo "New MINIO_SECRET_KEY: $MINIO_SECRET_KEY"
   ```
2. Update MinIO console:
   - Navigate to MinIO dashboard
   - Go to **Access Keys**
   - Create new access key with new credentials
   - Grant appropriate permissions
3. Update `.env.production`:
   ```bash
   echo "MINIO_ROOT_USER=$MINIO_ACCESS_KEY" >> .env.production
   echo "MINIO_ROOT_PASSWORD=$MINIO_SECRET_KEY" >> .env.production
   ```
4. Update Docker Compose (if used):
   ```yaml
   minio:
     environment:
       MINIO_ROOT_USER: "$MINIO_ACCESS_KEY"
       MINIO_ROOT_PASSWORD: "$MINIO_SECRET_KEY"
   ```
5. Restart services:
   ```bash
   docker-compose restart minio backend
   ```
6. Verify MinIO connectivity:
   ```bash
   docker-compose exec backend python -c "
   import boto3
   import os
   s3 = boto3.client(
       's3',
       endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://localhost:9000'),
       aws_access_key_id=os.getenv('MINIO_ROOT_USER'),
       aws_secret_access_key=os.getenv('MINIO_ROOT_PASSWORD'),
       aws_session_token=None,
       config=boto3.session.Config(signature_version='s3v4'),
   )
   s3.list_buckets()
   print('MinIO connection successful')
   "
   ```

---

### SMTP Credentials

#### Secure Generation

SMTP credentials are typically generated by your email provider. Use their dashboard to create new credentials.

#### Where to Update

| Location | Update Method |
|----------|--------------|
| `.env.development` | Update `SMTP_USERNAME` and `SMTP_PASSWORD` |
| `.env.production` | Update `SMTP_USERNAME` and `SMTP_PASSWORD` |
| Email Provider Dashboard | Update credentials in provider dashboard |
| Docker Compose | Update in `docker-compose.yml` |

#### Services Need Restart

| Service | Restart Required | Command |
|---------|-----------------|---------|
| Backend API | Yes | `docker-compose restart backend` |

#### Migration Steps

1. Log in to your email provider dashboard (Gmail, SendGrid, Amazon SES, etc.)
2. Navigate to API keys or app passwords section
3. Create new API key or app password
4. Copy the credentials
5. Update `.env.production`:
   ```bash
   echo "SMTP_USERNAME=your-username-or-api-key" >> .env.production
   echo "SMTP_PASSWORD=your-password-or-app-password" >> .env.production
   ```
6. Update any environment-specific files
7. Restart backend services:
   ```bash
   docker-compose restart backend
   ```
8. Test email functionality:
   ```bash
   docker-compose exec backend python -c "
   import smtplib
   import os
   from email.message import EmailMessage
   
   msg = EmailMessage()
   msg['From'] = os.getenv('SMTP_FROM_EMAIL')
   msg['To'] = os.getenv('SMTP_FROM_EMAIL')
   msg['Subject'] = 'Test Email'
   msg.set_content('This is a test email to verify SMTP configuration.')
   
   with smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT', 587))) as smtp:
       smtp.starttls()
       smtp.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
       smtp.send_message(msg)
   
   print('Test email sent successfully')
   "
   ```

---

### Grafana Admin Password

#### Secure Generation

```bash
# Generate password
openssl rand -base64 24 | tr -d '\n' && echo

# Fallback
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

#### Where to Update

| Location | Update Method |
|----------|--------------|
| Grafana UI | Admin panel → Users |
| `.env.production` | Update `GRAFANA_ADMIN_PASSWORD` |
| Docker Compose | Update in `docker-compose.yml` |
| Kubernetes Secrets | Update in Grafana config |

#### Services Need Restart

| Service | Restart Required | Command |
|---------|-----------------|---------|
| Grafana | Yes | `docker-compose restart grafana` |

#### Migration Steps

1. Generate new password:
   ```bash
   GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 24 | tr -d '\n')
   echo "New GRAFANA_ADMIN_PASSWORD: $GRAFANA_ADMIN_PASSWORD"
   ```
2. Log in to Grafana UI as admin
3. Navigate to **Admin** → **Users**
4. Find the admin user and click **Edit**
5. Update password field
6. Alternatively, update environment variables and restart:
   ```bash
   echo "GRAFANA_ADMIN_USER=admin" >> .env.production
   echo "GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD" >> .env.production
   ```
7. Restart Grafana:
   ```bash
   docker-compose restart grafana
   ```
8. Verify admin login with new password

---

## Verifying Rotation Success

### Automated Verification Checklist

Create a verification script:

```bash
#!/bin/bash
# scripts/verify-rotation.sh

echo "=== Credential Rotation Verification ==="

# Database
echo -n "Database: "
docker-compose exec -T backend python -c "
import os, psycopg2
try:
    psycopg2.connect(os.getenv('DATABASE_URL'))
    print('✅ Connected')
except Exception as e:
    print(f'❌ Failed: {e}')
"

# JWT
echo -n "JWT: "
docker-compose exec -T backend python -c "
import jwt
import os
try:
    token = jwt.encode({'test': 'data'}, os.getenv('JWT_SECRET'), algorithm='HS256')
    jwt.decode(token, os.getenv('JWT_SECRET'), algorithms=['HS256'])
    print('✅ Working')
except Exception as e:
    print(f'❌ Failed: {e}')
"

# MinIO
echo -n "MinIO: "
docker-compose exec -T backend python -c "
import boto3, os
try:
    s3 = boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT', 'http://localhost:9000'),
        aws_access_key_id=os.getenv('MINIO_ROOT_USER'),
        aws_secret_access_key=os.getenv('MINIO_ROOT_PASSWORD'),
    )
    s3.list_buckets()
    print('✅ Connected')
except Exception as e:
    print(f'❌ Failed: {e}')
" 2>/dev/null || echo "⚠️  Skipped (not configured)"

# SMTP
echo -n "SMTP: "
docker-compose exec -T backend python -c "
import smtplib, os
try:
    with smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT', 587))) as smtp:
        smtp.starttls()
        smtp.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
        print('✅ Connected')
except Exception as e:
    print(f'❌ Failed: {e}')
" 2>/dev/null || echo "⚠️  Skipped (not configured)"

# OpenAI API
echo -n "OpenAI: "
docker-compose exec -T backend python -c "
import requests, os
try:
    headers = {'Authorization': f'Bearer {os.getenv(\"OPENAI_API_KEY\")}'}
    requests.get('https://api.openai.com/v1/models', headers=headers, timeout=5)
    print('✅ Connected')
except Exception as e:
    print(f'❌ Failed: {e}')
" 2>/dev/null || echo "⚠️  Skipped (not configured)"

echo "=== Verification Complete ==="
```

### Manual Verification Steps

1. **Check Logs**: Verify no authentication errors
   ```bash
   docker-compose logs backend | grep -i "auth\|error\|login"
   ```
2. **Test Endpoints**: Hit authentication endpoints
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"password"}'
   ```
3. **Verify Sessions**: Check session storage
   ```bash
   docker-compose exec redis redis-cli keys "*"
   ```
4. **Check Encryption**: Test data encryption
   ```bash
   docker-compose exec backend python -c "
   from app.services.encryption import EncryptionService
   enc = EncryptionService()
   test = 'secret data'
   assert enc.decrypt(enc.encrypt(test)) == test
   print('Encryption verified')
   "
   ```

---

## Multi-Service Rotation Scenarios

### Full Environment Rotation

Rotate all credentials at once for maximum security:

```bash
#!/bin/bash
# scripts/rotate-all.sh

set -e

echo "=== Starting Full Credential Rotation ==="

# 1. Generate all new credentials
JWT_SECRET=$(openssl rand -hex 32)
SESSION_SECRET=$(openssl rand -base64 32 | tr -d '\n')
ENCRYPTION_KEY=$(openssl rand -base64 32 | tr -d '\n')
MINIO_ACCESS_KEY=$(openssl rand -base64 20 | tr -d '\n' | head -c 20)
MINIO_SECRET_KEY=$(openssl rand -base64 60 | tr -d '\n' | head -c 40)

echo "Generated new credentials"
echo "WARNING: These values are printed to terminal. Securely store them!"

# 2. Update .env.production
cat >> .env.production << EOF
JWT_SECRET=$JWT_SECRET
SESSION_SECRET=$SESSION_SECRET
ENCRYPTION_KEY=$ENCRYPTION_KEY
MINIO_ROOT_USER=$MINIO_ACCESS_KEY
MINIO_ROOT_PASSWORD=$MINIO_SECRET_KEY
EOF

# 3. Update Kubernetes (if applicable)
kubectl create secret generic nebula-all-secrets \
  --from-literal=jwt-secret="$JWT_SECRET" \
  --from-literal=session-secret="$SESSION_SECRET" \
  --from-literal=encryption-key="$ENCRYPTION_KEY" \
  --from-literal=minio-access-key="$MINIO_ACCESS_KEY" \
  --from-literal=minio-secret-key="$MINIO_SECRET_KEY" \
  --from-literal=database-password="$DATABASE_PASSWORD" \
  -n nebula \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Update environment files
echo "Please update .env.development with the new values above"

# 5. Restart services
echo "Restarting services..."
docker-compose restart

# 6. Verify
echo "Verifying rotation..."
./scripts/verify-rotation.sh

echo "=== Full Rotation Complete ==="
echo "IMPORTANT: Update these credentials in provider dashboards:"
echo "- OpenAI API Key"
echo "- Brave API Key"
echo "- SerpAPI Key"
echo "- Google OAuth Credentials"
echo "- GitHub OAuth Credentials"
echo "- SMTP Credentials"
```

### Staged Rotation (Zero-Downtime)

For production environments requiring zero downtime:

1. **Phase 1**: Update credentials in staging environment
2. **Phase 2**: Deploy new configuration to production (services read new config)
3. **Phase 3**: Verify all services using new credentials
4. **Phase 4**: Gradually rotate credentials in external services
5. **Phase 5**: Monitor for any issues

---

## Emergency Response Procedures

### Compromised Credential Response Checklist

When a credential is suspected to be compromised:

1. **Immediate Actions**
   ```bash
   # Note the time and credential type
   echo "$(date): Credential compromise reported - [CREDENTIAL_TYPE]"
   
   # Generate new credential immediately
   NEW_CREDENTIAL=$(openssl rand -hex 32)
   echo "New credential generated"
   ```

2. **Document the Incident**
   - When was the compromise detected?
   - When was the credential created?
   - Who had access?
   - What systems are affected?
   - What data might be exposed?

3. **Create Incident Ticket**
   ```markdown
   # Incident: [Credential Type] Compromise
   
   ## Timeline
   - Detected: [Timestamp]
   - Responded: [Timestamp]
   - Resolved: [Timestamp]
   
   ## Affected Systems
   - [System 1]
   - [System 2]
   
   ## Actions Taken
   - [ ] Generated new credential
   - [ ] Updated all environments
   - [ ] Restarted affected services
   - [ ] Revoked old credential at provider
   - [ ] Verified rotation success
   ```

4. **Provider-Specific Revocation**

   | Provider | Revocation Link |
   |----------|----------------|
   | OpenAI | [API Keys](https://platform.openai.com/api-keys) |
   | GitHub | [Developer Settings](https://github.com/settings/developers) |
   | Google | [Cloud Console](https://console.cloud.google.com/apis/credentials) |
   | AWS | [IAM Console](https://console.aws.amazon.com/iam/home) |

5. **Post-Incident Steps**
   - Rotate all potentially exposed credentials
   - Review access logs for unauthorized access
   - Update monitoring alerts
   - Document lessons learned
   - Update incident response procedures

### Compromised JWT Secret Emergency Rotation

1. Generate new JWT secret
2. Update all environments
3. Revoke all active sessions (delete Redis session data)
4. Force all users to log in again
5. Monitor for authentication failures
6. Check for suspicious login patterns

### Compromised Database Password Emergency Rotation

1. Generate new database password
2. Update database user password
3. Update all application environments
4. Restart all services
5. Verify database connectivity
6. Check for unauthorized queries in database logs
7. Review and revoke any suspicious database permissions

---

## Automation Suggestions

### Pre-Rotation Automation

1. **Credential Inventory Script**
   ```bash
   # scripts/credential-inventory.sh
   # Scans codebase for credential patterns
   grep -r "JWT_SECRET\|SESSION_SECRET\|OPENAI_API_KEY" .env* --include="*.env*" | grep -v "change-me"
   ```

2. **Pre-Rotation Validation**
   ```bash
   # scripts/pre-rotation-check.sh
   # Checks if all dependencies support credential updates
   # Verifies no hardcoded credentials in code
   ```

### Rotation Automation

1. **Secrets Management Integration**
   - HashiCorp Vault
   - AWS Secrets Manager
   - Azure Key Vault
   - Google Secret Manager

2. **Scheduled Rotation**
   ```bash
   # cron job for quarterly rotation
   0 2 1 */3 * /path/to/scripts/rotate-all.sh >> /var/log/rotation.log 2>&1
   ```

3. **CI/CD Integration**
   ```yaml
   # .github/workflows/rotate-secrets.yml
   name: Rotate Credentials
   on:
     schedule:
       - cron: '0 2 1 */3 *'  # Quarterly
   jobs:
     rotate:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Generate New Secrets
           run: |
             echo "JWT_SECRET=$(openssl rand -hex 32)" >> $GITHUB_ENV
         - name: Update Repository Secrets
           uses: github-actions-secrets-manager/rotate@v1
           with:
             secret-name: JWT_SECRET
   ```

### Post-Rotation Automation

1. **Automated Verification**
   ```bash
   # scripts/verify-all.sh
   # Runs all verification checks
   # Alerts on any failures
   ```

2. **Monitoring Alerts**
   - Authentication failure rate
   - Database connection failures
   - API key errors
   - Email delivery failures

3. **Log Aggregation**
   - Send rotation events to SIEM
   - Create audit trail
   - Alert on suspicious patterns

---

## Additional Resources

### Tools

| Tool | Purpose | Link |
|------|---------|------|
| HashiCorp Vault | Secrets management | [vaultproject.io](https://www.vaultproject.io) |
| AWS Secrets Manager | AWS secrets management | [aws.amazon.com/secrets-manager](https://aws.amazon.com/secrets-manager) |
| Doppler | Developer secrets management | [doppler.com](https://doppler.com) |
| 1Password CLI | CLI secrets management | [1password.com/cli](https://1password.com/cli) |

### Documentation

- [OWASP Secret Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html) - Authentication
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)

### Contact

For security incidents or questions:
- Security Team: security@example.com
- On-Call: +1-555-SEC-OPS

---

*Last Updated: $(date +%Y-%m-%d)*
*Version: 1.0*
