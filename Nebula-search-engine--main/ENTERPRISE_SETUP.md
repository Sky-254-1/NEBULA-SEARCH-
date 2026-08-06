# Enterprise Features Setup Guide

This document provides step-by-step instructions for configuring enterprise features in Nebula Search.

## Table of Contents
1. [SAML 2.0 SSO](#saml-20-sso)
2. [WebAuthn Biometric Authentication](#webauthn-biometric-authentication)
3. [Push Notifications (FCM/APNs)](#push-notifications-fcmapns)
4. [Document Preview](#document-preview)
5. [Federated Search](#federated-search)
6. [Plugin System](#plugin-system)

---

## SAML 2.0 SSO

### Prerequisites
- SAML 2.0 Identity Provider (IdP) such as Azure AD, Okta, Auth0, or Keycloak
- `python3-saml` library installed: `pip install python3-saml`

### Configuration

1. **Enable SAML in `.env`:**
```env
ENABLE_SAML=true
SAML_ENTITY_ID=nebula-search
SAML_METADATA_URL=https://your-idp.example.com/metadata
SAML_CERT_PATH=/path/to/saml_cert.pem
SAML_KEY_PATH=/path/to/saml_key.pem
```

2. **Configure your IdP:**
   - Set the Assertion Consumer Service (ACS) URL: `https://your-domain.com/api/v1/auth/saml/acs`
   - Set the Entity ID: `nebula-search`
   - Upload your SP certificate (or use IdP-managed certificates)
   - Configure attribute mapping:
     - `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress` → user email
     - `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name` → user name

3. **API Endpoints:**
   - `GET /api/v1/auth/saml/login` - Initiate SAML login
   - `POST /api/v1/auth/saml/acs` - SAML assertion consumer service
   - `GET /api/v1/auth/saml/metadata` - SP metadata XML
   - `POST /api/v1/auth/saml/logout` - SAML logout

### Example Usage
```bash
# Get SAML authorization URL
curl https://your-domain.com/api/v1/auth/saml/login

# Redirect user to the returned authorization_url
# After IdP authentication, user is redirected back to ACS endpoint
# ACS returns JWT tokens
```

---

## WebAuthn Biometric Authentication

### Prerequisites
- `webauthn` library installed: `pip install webauthn`

### Mobile Biometric Auth (Capacitor)

For native iOS/Android apps built with Capacitor:

```bash
npm install @capacitor-community/biometric
npx cap sync
```

Example usage:

```typescript
const result = await BiometricAuth.checkBiometric({
  biometricReason: 'Authenticate to access Nebula Search',
  allowDeviceCredentialFallback: true,
});

if (result.isAvailable) {
  // Use backend WebAuthn endpoints:
  // POST /api/v1/auth/webauthn/login/start
  // POST /api/v1/auth/webauthn/login/complete
}
```

### Configuration

1. **Enable WebAuthn in `.env`:**
```env
ENABLE_WEBAUTHN=true
WEBAUTHN_RP_ID=your-domain.com
WEBAUTHN_RP_NAME=Nebula Search
```

2. **Frontend Integration:**
   - Use the WebAuthn API in the browser:
   ```javascript
   // Register new credential
   const challenge = await fetch('/api/v1/auth/webauthn/register/start', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({username: user.email})
   }).then(r => r.json());
   
   const credential = await navigator.credentials.create({
     publicKey: {
       challenge: base64ToArrayBuffer(challenge.challenge),
       rp: challenge.rp,
       user: challenge.user,
       pubKeyCredParams: challenge.pubKeyCredParams,
     }
   });
   
   await fetch('/api/v1/auth/webauthn/register/complete', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({
       credential_id: arrayBufferToBase64(credential.rawId),
       public_key: arrayBufferToBase64(credential.response.publicKey),
       sign_count: credential.response.signCount,
       attestation_object: arrayBufferToBase64(credential.response.attestationObject),
       client_data_json: arrayBufferToBase64(credential.response.clientDataJSON),
     })
   });
   ```

3. **API Endpoints:**
   - `POST /api/v1/auth/webauthn/register/start` - Start registration
   - `POST /api/v1/auth/webauthn/register/complete` - Complete registration
   - `POST /api/v1/auth/webauthn/login/start` - Start login
   - `POST /api/v1/auth/webauthn/login/complete` - Complete login
   - `DELETE /api/v1/auth/webauthn/credential` - Remove credential

---

## Push Notifications (FCM/APNs)

### Prerequisites
- Firebase project for Android/Web push notifications
- Apple Developer account for iOS push notifications

### Configuration

1. **Enable Push Notifications in `.env`:**
```env
ENABLE_PUSH_NOTIFICATIONS=true
FCM_SERVER_KEY=your_fcm_server_key
FCM_PROJECT_ID=your_fcm_project_id
APNS_KEY_ID=your_apns_key_id
APNS_TEAM_ID=your_apns_team_id
APNS_BUNDLE_ID=com.nebula.search
```

2. **Firebase Setup (Android/Web):**
   - Create a Firebase project at https://console.firebase.google.com
   - Add Android/iOS/Web app to your project
   - Download `google-services.json` (Android) or `GoogleService-Info.plist` (iOS)
   - Get the FCM Server Key from Project Settings → Cloud Messaging

3. **Apple Push Notifications (iOS):**
   - Create an App ID in Apple Developer Portal
   - Enable Push Notifications capability
   - Create an APNs Auth Key (.p8 file)
   - Note the Key ID and Team ID

4. **Frontend Integration:**
```javascript
// Register for push notifications
const token = await pushManager.getSubscription().then(...);

await fetch('/api/v1/notifications/push/register', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    token: token,
    platform: 'web', // 'ios', 'android', or 'web'
    device_id: 'unique-device-id'
  })
});
```

5. **API Endpoints:**
   - `POST /api/v1/notifications/push/register` - Register push token
   - `DELETE /api/v1/notifications/push/unregister` - Unregister token
   - `POST /api/v1/notifications/push/send` - Send notification
   - `GET /api/v1/notifications/push/status` - Check registration status

---

## Document Preview

### Configuration

1. **Enable Document Preview in `.env`:**
```env
ENABLE_DOCUMENT_PREVIEW=true
MAX_PREVIEW_SIZE_MB=50
```

2. **Supported File Types:**
   - Images: `image/*` (direct streaming)
   - PDFs: `application/pdf` (direct streaming)
   - Text: `text/*`, `application/json`, `application/javascript` (content returned as JSON)
   - Other: Metadata only (preview not available)

3. **API Endpoints:**
   - `GET /api/v1/documents/preview/{document_id}` - Get document preview
   - `GET /api/v1/documents/preview/{document_id}/metadata` - Get document metadata

### Example Usage
```bash
# Get document preview
curl -H "Authorization: Bearer {token}" \
  https://your-domain.com/api/v1/documents/preview/123

# Response for images/PDFs: binary file stream
# Response for text: {"content": "...", "content_type": "text/plain"}
# Response for unsupported: {"preview_available": false, "message": "..."}
```

---

## Federated Search

### Configuration

1. **Enable Federated Search in `.env`:**
```env
ENABLE_FEDERATED_SEARCH=true
```

2. **How It Works:**
   - Users can search across multiple devices/sessions
   - Each device registers a session with a unique `session_id`
   - Search queries are broadcast to all active sessions
   - Results are aggregated and returned

3. **API Endpoints:**
   - `POST /api/v1/search/federated/search` - Search across devices
   - `GET /api/v1/search/federated/devices` - List user's devices
   - `DELETE /api/v1/search/federated/devices/{session_id}` - Remove device

### Example Usage
```bash
# Search across all devices
curl -X POST https://your-domain.com/api/v1/search/federated/search \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "include_history": true}'

# List registered devices
curl https://your-domain.com/api/v1/search/federated/devices \
  -H "Authorization: Bearer {token}"

# Remove a device
curl -X DELETE https://your-domain.com/api/v1/search/federated/devices/abc123 \
  -H "Authorization: Bearer {token}"
```

---

## Plugin System

### Architecture

The plugin system allows you to add new search providers without modifying core code.

### Creating a Custom Plugin

1. **Create a new file in `backend/app/plugins/providers/`:**
```python
# backend/app/plugins/providers/myprovider.py
from app.plugins.base import SearchProvider, SearchRequest, SearchResult
import httpx

class MyProvider(SearchProvider):
    @property
    def name(self) -> str:
        return "myprovider"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    async def search(self, request: SearchRequest) -> list[SearchResult]:
        # Your search logic here
        api_key = os.getenv("MYPROVIDER_API_KEY")
        # ... implement search
        return results
    
    async def health_check(self) -> bool:
        return bool(os.getenv("MYPROVIDER_API_KEY"))
```

2. **Register the plugin in `backend/app/plugins/__init__.py`:**
```python
providers = [
    # ... existing providers
    ("myprovider", "app.plugins.providers.myprovider", "MyProvider"),
]
```

3. **Using the plugin:**
```python
from app.plugins import get_plugin_manager, load_plugins

load_plugins()  # Load all plugins
pm = get_plugin_manager()

# Search using specific provider
results = await pm.search("myprovider", request)

# Federated search across all providers
all_results = await pm.federated_search(request)
```

### Built-in Plugins

| Provider | Environment Variable | Status |
|----------|---------------------|--------|
| Brave | `BRAVE_API_KEY` | ✅ Active |
| Google | `GOOGLE_API_KEY`, `GOOGLE_SEARCH_CX` | ✅ Active |
| Bing | `BING_API_KEY` | ✅ Active |
| DuckDuckGo | None required | ✅ Active |

### Plugin API Reference

**SearchRequest:**
- `query: str` - Search query
- `max_results: int` - Maximum number of results (default: 10)
- `filters: Optional[dict]` - Optional filters
- `user_id: Optional[str]` - User ID for personalization

**SearchResult:**
- `title: str` - Result title
- `url: Optional[str]` - Result URL
- `snippet: str` - Result description/snippet
- `score: float` - Relevance score (0.0 to 1.0)
- `metadata: Optional[dict]` - Additional metadata
- `source: str` - Provider name

**SearchProvider (Abstract Base Class):**
- `name: str` - Provider name
- `version: str` - Provider version
- `search(request: SearchRequest) -> list[SearchResult]` - Execute search
- `health_check() -> bool` - Check if provider is available

---

## General Notes

- All enterprise features are **disabled by default** and must be explicitly enabled via environment variables
- Features can be enabled independently without affecting existing functionality
- All new routes are protected by existing authentication middleware
- In production, use Redis for challenge storage (WebAuthn, SAML) instead of in-memory dictionaries
- Implement proper error handling and logging for production deployments

## Testing

```bash
# Run all backend tests
cd backend && python -m pytest tests/ -v

# Run specific test suites
python -m pytest tests/test_analytics.py -v
python -m pytest tests/test_auth_extended.py -v
```

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify environment variables are set correctly
3. Ensure all dependencies are installed: `pip install -r requirements.txt`
4. Consult the API documentation at https://your-domain.com/docs