# Nebula Search Engine - Authentication & Authorization API Documentation

## Overview

The Nebula Search Engine provides a comprehensive, enterprise-grade authentication and authorization system with support for:

- **Local Authentication**: Email/password with secure hashing
- **JWT Tokens**: Access and refresh tokens with rotation
- **Email Verification**: Secure email verification flow
- **Password Reset**: Secure password recovery
- **Multi-Factor Authentication (MFA)**: TOTP authenticator apps with backup codes
- **OAuth Integration**: Google, GitHub, Microsoft, Apple
- **Session Management**: Multiple active sessions with device tracking
- **Role-Based Access Control (RBAC)**: Granular permission system
- **Audit Logging**: Comprehensive security event logging

## Base URL

```
/api/v1/auth
```

## Authentication

All protected endpoints require a valid JWT access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

Alternatively, when `AUTH_COOKIE_MODE=true`, tokens can be sent via HTTP-only cookies.

## Endpoints

### User Registration

#### POST /signup

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (201 Created):**
```json
{
  "message": "User created successfully. Please check your email to verify your account."
}
```

**Password Requirements:**
- Minimum 8 characters, maximum 128 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character (!@#$%^&*(),.?":{}|<>)
- Cannot match email
- Cannot be common password

**Rate Limit:** 5 requests per minute per IP/email

---

### User Login

#### POST /login

Authenticate user and receive access/refresh tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Features:**
- Brute force protection (5 attempts, 15 min lockout)
- Exponential backoff on failures
- Session creation with device tracking
- Refresh token rotation
- Audit logging

**Rate Limit:** 5 requests per minute per IP/email

---

### Refresh Token

#### POST /refresh

Get new access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Features:**
- Refresh token rotation (old token invalidated)
- Reuse detection (revokes entire session family)
- Session family tracking

**Rate Limit:** 10 requests per minute

---

### Logout

#### POST /logout

Logout current session.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "message": "Logged out"
}
```

**Features:**
- Deletes entire session family
- Clears cookies (if cookie mode enabled)
- Audit logging

---

### Logout All Sessions

#### POST /logout-all

Logout from all devices.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Logged out from all devices"
}
```

**Features:**
- Deletes all user sessions
- Clears cookies
- Audit logging

---

### Get Current User

#### GET /me

Get current user information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "email": "user@example.com",
  "role": "user",
  "email_verified": true,
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-02T00:00:00Z"
}
```

---

## Email Verification

### Verify Email

#### GET /verify-email

Verify email address using token.

**Query Parameters:**
- `token` (required): Verification token

**Response (200 OK):**
```json
{
  "message": "Email verified successfully"
}
```

**Features:**
- Single-use token
- 24-hour expiration
- Invalidates other unused tokens

---

### Resend Verification

#### POST /resend-verification

Resend email verification link.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Verification email sent"
}
```

**Features:**
- Rate limited
- Creates new token
- Invalidates old tokens

---

## Password Reset

### Forgot Password

#### POST /forgot-password

Request password reset link.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "If an account exists, a reset link has been sent"
}
```

**Features:**
- Prevents email enumeration (always returns success)
- 1-hour token expiration
- Single-use token
- Audit logging

---

### Reset Password

#### POST /reset-password

Reset password using token.

**Request Parameters:**
- `token` (required): Reset token
- `new_password` (required): New password

**Response (200 OK):**
```json
{
  "message": "Password reset successful. Please log in with your new password."
}
```

**Features:**
- Invalidates all user sessions
- Invalidates other unused reset tokens
- Password validation enforced
- Audit logging

---

## Account Management

### Change Password

#### POST /change-password

Change password for authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Parameters:**
- `current_password` (required): Current password
- `new_password` (required): New password

**Response (200 OK):**
```json
{
  "message": "Password changed successfully. Please log in again."
}
```

**Features:**
- Requires current password verification
- Invalidates all sessions
- Password validation enforced
- Audit logging

---

### Change Email

#### POST /change-email

Change email address for authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Parameters:**
- `new_email` (required): New email address
- `password` (required): Current password

**Response (200 OK):**
```json
{
  "message": "Verification email sent to new address. Please verify to complete the change."
}
```

**Features:**
- Requires password verification
- Checks for duplicate email
- Sends verification to new email
- Audit logging

---

### Delete Account

#### DELETE /account

Delete user account.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Parameters:**
- `password` (required): Current password

**Response (200 OK):**
```json
{
  "message": "Account deleted successfully"
}
```

**Features:**
- Soft delete (GDPR compliant)
- Deletes all sessions
- Audit logging

---

## Session Management

### Get Active Sessions

#### GET /sessions

Get all active sessions for current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "sessions": [
    {
      "session_id": "uuid",
      "device_name": "Mozilla/5.0...",
      "ip_address": "192.168.1.1",
      "created_at": "2024-01-01T00:00:00Z",
      "last_activity_at": "2024-01-02T00:00:00Z",
      "expires_at": "2024-01-08T00:00:00Z"
    }
  ]
}
```

---

### Terminate Session

#### DELETE /sessions/{session_id}

Terminate a specific session.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Session terminated"
}
```

**Features:**
- Only owner can terminate
- Audit logging

---

## Multi-Factor Authentication (MFA)

### Setup MFA

#### POST /mfa/setup

Setup MFA for current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANS...",
  "backup_codes": ["ABCD-1234", "EFGH-5678", ...],
  "message": "Scan the QR code with your authenticator app and enter the code to verify"
}
```

**Features:**
- Generates TOTP secret
- QR code for easy setup
- 10 backup recovery codes
- 10-minute expiration for setup

---

### Verify MFA Setup

#### POST /mfa/verify

Verify MFA setup with token.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Parameters:**
- `token` (required): 6-digit TOTP code

**Response (200 OK):**
```json
{
  "message": "MFA enabled successfully",
  "backup_codes": ["ABCD-1234", "EFGH-5678", ...]
}
```

**Features:**
- Validates TOTP token
- Saves MFA settings
- Sends notification email
- Returns backup codes (only shown once)

---

### Verify MFA Token

#### POST /mfa/verify-token

Verify MFA token during login.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Parameters:**
- `token` (required): 6-digit TOTP code or backup code

**Response (200 OK):**
```json
{
  "message": "MFA token verified"
}
```

**Features:**
- Accepts TOTP tokens
- Accepts backup codes (single-use)
- Marks session as MFA-verified

---

### Disable MFA

#### POST /mfa/disable

Disable MFA for current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Parameters:**
- `password` (required): Current password

**Response (200 OK):**
```json
{
  "message": "MFA disabled successfully"
}
```

**Features:**
- Requires password verification
- Removes MFA settings
- Audit logging

---

### Regenerate Backup Codes

#### POST /mfa/regenerate-backup-codes

Regenerate backup codes.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Backup codes regenerated",
  "backup_codes": ["ABCD-1234", "EFGH-5678", ...]
}
```

**Features:**
- Invalidates old backup codes
- Returns new codes (only shown once)

---

### Get MFA Status

#### GET /mfa/status

Get MFA status for current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "mfa_enabled": true,
  "has_backup_codes": true
}
```

---

## OAuth Integration

### Get Authorization URL

#### GET /oauth/{provider}/authorize

Get OAuth authorization URL.

**Path Parameters:**
- `provider` (required): OAuth provider (google, github, microsoft, apple)

**Response (200 OK):**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "random_state_token"
}
```

**Supported Providers:**
- `google`
- `github`
- `microsoft`
- `apple`

---

### OAuth Callback

#### GET /oauth/{provider}/callback

Handle OAuth callback (automatically called by provider).

**Query Parameters:**
- `code` (required): Authorization code
- `state` (required): State parameter

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "email": "user@example.com",
    "role": "user"
  }
}
```

**Features:**
- Creates new user if doesn't exist
- Links OAuth account to existing user
- Prevents duplicate accounts
- Creates session and tokens

---

### Link OAuth Account

#### POST /oauth/link

Link OAuth account to current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Parameters:**
- `provider` (required): OAuth provider
- `code` (required): Authorization code

**Response (200 OK):**
```json
{
  "message": "OAuth account linked to google"
}
```

---

### Unlink OAuth Account

#### DELETE /oauth/unlink

Unlink OAuth account from current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Parameters:**
- `provider` (required): OAuth provider

**Response (200 OK):**
```json
{
  "message": "OAuth account unlinked from google"
}
```

**Features:**
- Requires password to be set
- Cannot unlink if it's the only login method

---

### Get Linked OAuth Accounts

#### GET /oauth/accounts

Get linked OAuth accounts for current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "accounts": [
    {
      "provider": "google",
      "provider_user_id": "123456789",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

## Error Responses

All endpoints return standard HTTP error codes:

**400 Bad Request:**
```json
{
  "detail": "Invalid request parameters"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Invalid or expired token"
}
```

**403 Forbidden:**
```json
{
  "detail": "Permission denied"
}
```

**404 Not Found:**
```json
{
  "detail": "Resource not found"
}
```

**409 Conflict:**
```json
{
  "detail": "Email already registered"
}
```

**429 Too Many Requests:**
```json
{
  "detail": "Rate limit exceeded. Try again shortly."
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error"
}
```

---

## Security Features

### JWT Tokens

- **Access Tokens**: Short-lived (default 30 minutes)
- **Refresh Tokens**: Long-lived (default 7 days)
- **Token Rotation**: Refresh tokens rotated on each use
- **Reuse Detection**: Detects and prevents token reuse
- **Audience Validation**: Validates token audience
- **Issuer Validation**: Validates token issuer
- **JWT ID**: Unique identifier for each token

### Password Security

- **Hashing**: PBKDF2-HMAC-SHA256 with 200,000 iterations
- **Salt**: 16-byte random salt per password
- **Validation**: Strong password policy enforced
- **Comparison**: Timing-safe comparison

### Session Security

- **Token Hashing**: Refresh tokens hashed in database
- **Session Tracking**: Device, IP, and user agent tracking
- **Session Expiration**: Automatic expiration
- **Session Revocation**: Manual and automatic revocation
- **Family Tracking**: Token rotation family tracking

### Brute Force Protection

- **Rate Limiting**: Per-endpoint rate limiting
- **Account Lockout**: Temporary lockout after failed attempts
- **Exponential Backoff**: Increasing delays on failures
- **IP Tracking**: IP-based attempt tracking

### Audit Logging

All security events are logged:
- Registration
- Login/Logout
- Failed login attempts
- Password reset
- Email verification
- MFA enrollment/verification
- Token refresh
- Session termination
- Account changes

---

## Configuration

### Environment Variables

```env
# JWT Configuration
JWT_SECRET=your-secret-key-here
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

# MFA
ENABLE_MFA=false
MFA_ISSUER=Nebula Search

# OAuth
ENABLE_OAUTH=false
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=
APPLE_CLIENT_ID=
APPLE_CLIENT_SECRET=

# Email Service
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_FROM_NAME=Nebula Search
SMTP_USE_TLS=true

# Audit Logging
ENABLE_AUDIT_LOGS=true
```

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| /signup | 5 requests | 1 minute |
| /login | 5 requests | 1 minute |
| /refresh | 10 requests | 1 minute |
| /forgot-password | 3 requests | 1 minute |
| /resend-verification | 3 requests | 1 minute |

---

## Best Practices

1. **Store tokens securely**: Use HTTP-only cookies or secure storage
2. **Use HTTPS**: Always use HTTPS in production
3. **Enable MFA**: Encourage users to enable MFA
4. **Monitor audit logs**: Regularly review security events
5. **Rotate secrets**: Regularly rotate JWT secrets and API keys
6. **Set strong passwords**: Enforce password policy
7. **Verify emails**: Require email verification for sensitive operations
8. **Use short-lived tokens**: Keep access token TTL short
9. **Implement CSRF protection**: Use CSRF tokens for cookie-based auth
10. **Rate limiting**: Keep rate limits enabled

---

## Testing

Use the provided test suite to verify authentication flows:

```bash
# Run auth tests
pytest tests/test_auth.py -v

# Run MFA tests
pytest tests/test_mfa.py -v

# Run OAuth tests
pytest tests/test_oauth.py -v
```

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/Sky-254-1/Nebula-search-engine-/issues
- Documentation: https://docs.nebula-search.io
- Email: support@nebula-search.io