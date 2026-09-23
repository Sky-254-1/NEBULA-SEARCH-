# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.1.x   | :white_check_mark: |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do NOT open a public issue for security vulnerabilities.**

Instead, email us at: **security@nebula-search.example.com**

We aim to respond to security reports within **48 hours** and provide an initial
action plan within **72 hours**.

### What to Include

When reporting a vulnerability, please include:

1. **Type of vulnerability** (e.g., XSS, SQL injection, privilege escalation)
2. **Steps to reproduce** with example payloads
3. **Potential impact** of the vulnerability
4. **Any mitigations** you've identified
5. Your GitHub username (for credit in our security advisory)

### Security Bounds

We take security seriously. When testing:

- ✅ Do test for security vulnerabilities
- ✅ Do provide detailed reproduction steps
- ❌ Do NOT test production systems without explicit permission
- ❌ Do NOT exploit vulnerabilities beyond demonstration
- ❌ Do NOT disclose vulnerabilities publicly before we've had time to address them

---

## Security Features

### Authentication & Authorization

- ✅ JWT-based authentication with HS256
- ✅ Refresh token rotation (prevents reuse)
- ✅ Token reuse detection with session family revocation
- ✅ RBAC (Role-Based Access Control) with admin/user roles
- ✅ Session tracking by device, IP, and user agent

### Data Protection

- ✅ PBKDF2-SHA256 password hashing (200k iterations, salted)
- ✅ Password complexity enforcement
- ✅ Brute-force protection (5 attempts, 15min lockout)
- ✅ SQL injection prevention via parameterized queries
- ✅ XSS protection via Pydantic validation
- ✅ Input sanitization (control char removal)

### API Security

- ✅ Security headers (X-Frame-Options, X-Content-Type-Options, Referrer-Policy)
- ✅ HSTS in production (`Strict-Transport-Security`)
- ✅ CORS restrictions (configurable origins)
- ✅ Rate limiting (Redis + in-memory fallback)
- ✅ Request ID propagation for tracing

### Infrastructure Security

- ✅ HTTPS/TLS for all production traffic
- ✅ Environment variables for secrets (never committed)
- ✅ Docker secrets support (via env file)
- ✅ Health checks for service monitoring
- ✅ Audit logging for security events

---

## Security Testing

### Automated

- **Static Analysis:** Ruff (Python), ESLint (JavaScript)
- **Dependency Scanning:** npm audit, pip audit
- **Secrets Detection:** Gitleaks, TruffleHog

### Manual (Recommended for Contributors)

Run these tests locally:

```bash
# Python dependency vulnerabilities
cd backend
pip install pip-audit
pip-audit

# JavaScript dependency vulnerabilities
cd frontend
npm audit

# Local security scan (requires TruffleHog)
trufflehog filesystem .
```

---

## Security Updates

Security patches are released as **patch version updates** (e.g., 1.0.1, 1.1.1).

### Subscription

To receive security notifications:

1. Watch the repository for "Releases only"
2. Subscribe to our security mailing list (email `security-subscribe@nebula-search.example.com`)
3. Follow our security advisories on GitHub

---

## Best Practices for Users

### For Self-Hosted Deployments

1. **Set strong `JWT_SECRET`**:
   ```bash
   # Generate a 64-character hex string
   openssl rand -hex 32
   ```

2. **Restrict CORS origins**:
   ```env
   CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
   ```

3. **Enable HTTPS** (required in production):
   - Use Let's Encrypt for free certificates
   - Configure HSTS headers

4. **Configure Redis** (recommended):
   ```env
   REDIS_URL=redis://user:password@redis-host:6379/0
   ```

5. **Enable audit logs**:
   ```env
   ENABLE_AUDIT_LOGS=true
   ```

### For API Consumers

1. **Use API keys securely**:
   - Store keys in environment variables
   - Never commit API keys to version control

2. **Implement retry logic**:
   ```javascript
   // Backoff strategy for rate limiting
   const retryWithBackoff = async (fn, maxRetries = 3) => {
     for (let i = 0; i < maxRetries; i++) {
       try {
         return await fn();
       } catch (e) {
         if (e.status === 429) {
           await sleep(2 ** i * 1000);
           continue;
         }
         throw e;
       }
     }
   };
   ```

3. **Validate responses**:
   - Check response status codes
   - Validate JSON structure
   - Handle rate limiting gracefully

---

## Security Contact

- **Email:** security@nebula-search.example.com
- **PGP Key:** Available upon request
- **Response Time:** 48 hours (initial), 72 hours (action plan)

---

## Acknowledgments

We thank the following security researchers for their responsible disclosure:

- [List of researchers - to be updated]

---

*Last updated: July 1, 2026*
