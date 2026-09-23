# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.2.x   | :white_check_mark: |
| < 1.2   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Nebula Search, please report it responsibly:

1. **Email**: Send details to security@nebula-search.example.com
2. **Encryption**: Use our PGP key (available on our website)
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Response Timeline

- **Initial response**: Within 48 hours
- **Status update**: Every 5 business days
- **Fix timeline**: Depends on severity
  - Critical: 1-7 days
  - High: 7-14 days
  - Medium: 14-30 days
  - Low: Next release

## Security Measures

### Application Security
- Input validation and sanitization
- SQL injection prevention (parameterized queries)
- XSS protection (CSP headers)
- CSRF tokens on state-changing operations
- Rate limiting per IP and user
- Audit logging for security events
- Password hashing with bcrypt
- JWT with short expiry + refresh tokens
- MFA support (TOTP)
- RBAC with least-privilege principle

### Infrastructure Security
- HTTPS/TLS 1.3 only
- WAF with rate limiting
- Private subnets for backend services
- Security groups limiting port exposure
- Encrypted data at rest (RDS, EBS)
- Encrypted secrets in SSM Parameter Store
- Docker containers run as non-root
- Read-only filesystems where possible
- Dropped Linux capabilities

### CI/CD Security
- Automated dependency scanning (Trivy)
- CodeQL security analysis
- Dependabot for dependency updates
- Required CI checks before merge
- Branch protection rules
- Signed commits (recommended)
- Secret scanning in GitHub

## Best Practices for Users

1. **Never expose** `.env` files or secrets in version control
2. **Rotate** JWT_SECRET and API keys regularly
3. **Use** strong, unique passwords for admin accounts
4. **Enable** MFA for all admin users
5. **Restrict** CORS_ORIGINS to your actual frontend domain
6. **Monitor** audit logs for suspicious activity
7. **Keep** dependencies updated via Dependabot
8. **Review** security scan results in CI/CD
9. **Backup** database regularly
10. **Use** HTTPS in production only

## Known Limitations

- SQLite mode does not support row-level security
- Rate limiting is per-IP in proxy mode (use Redis for per-user limits)
- Audit logs retained for 90 days only
- WAF rules may need customization for your region

## Security Update Policy

- Security patches are backported to the latest minor version
- Critical vulnerabilities trigger immediate patch releases
- Security advisories published on GitHub Security tab
- CVEs requested for publicly disclosed vulnerabilities