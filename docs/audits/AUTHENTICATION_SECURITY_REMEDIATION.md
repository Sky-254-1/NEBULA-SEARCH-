# Authentication, Authorization, Security and QA Audit

**Audit date:** 2026-10-30  
**Scope inspected:** FastAPI authentication/session services, JWT validation,
indexing routes and workers, document ownership, OAuth callback, crawler fetch,
browser auth store, database migrations, existing tests and API documentation.

## Status

This is a partial remediation. The highest-priority indexing ownership and
refresh-token family defects listed below have fixes and focused test results.
The repository does not yet meet the brief's production acceptance criteria.
OAuth/OIDC verification, API-client credentials, organization tenancy, upload
streaming/content inspection, crawler SSRF controls, GraphQL authorization and
production-wide CI verification remain open.

## Inventory

| Area | Audit result |
| --- | --- |
| Password login and signup | Implemented; password hashes use PBKDF2-HMAC-SHA256 (200,000 rounds), brute-force throttling, and database-backed sessions. Reset and verification repositories/routes exist; delivery and end-to-end coverage need separate review. |
| JWT | HMAC signature, configured algorithm, issuer, audience, expiry and access token checks exist. This change now rejects missing subjects and missing access-token type claims. Key rotation and asymmetric key management are not implemented. |
| Refresh sessions | Hashed opaque tokens and session repository exist. Rotation was not atomic and reuse revocation did not cover descendants; fixed with a compare-and-set update, family identifier migration, and family-wide revocation. |
| OAuth/OIDC | Provider endpoints exist but identity verification and account linking are unsafe. The callback links accounts by email without verifying provider email; PKCE, nonce, redirect allowlisting and OIDC ID-token verification are absent. |
| API clients | No separate client identity, secret lifecycle, scoped client credentials flow, or usage controls found in the inspected auth model. |
| Organizations | No tenant or organization model found. |
| Indexing authorization | Authentication existed, but document ownership was not checked and jobs were globally visible/cancellable. Fixed for the in-process queue and progress tracker. |
| Operational routes | Worker health and scheduler were available to ordinary authenticated users; now administrator-gated. Metrics and dead-letter routes are also administrator-gated. |
| Dead-letter operations | Retry/list/delete were success-shaped placeholders. They now return explicit `501 Not Implemented`; a durable repository and actual retry workflow remain unimplemented. |
| Documents/uploads | Document reads/deletes use owner-filtered queries. Upload currently reads the full request into memory and trusts extension/client MIME; streaming limits and content validation remain open. |
| Crawler | Fetch follows redirects without destination/IP revalidation. SSRF controls are absent in the inspected fetch path. |
| Browser credentials | The frontend auth store persists both access and refresh tokens in `localStorage`. HttpOnly cookie mode exists server-side, but the browser integration still uses bearer tokens and requires a coordinated migration. |
| GraphQL, CI, infrastructure | Not fully audited or verified in this change. Existing tests cover selected API behavior, but no CI run or production deployment verification was performed. |

## Remediated findings

| Severity | Root cause | Changed files | Test added / actual result |
| --- | --- | --- | --- |
| Critical | Indexing start/reindex trusted document IDs and jobs were not associated with users; job lookup/cancel used globally keyed in-memory progress. | `backend/app/routes/indexing.py`, `backend/app/indexing/progress.py` | `tests/test_indexing_authorization.py`: cross-user document submission and job read/cancel denied; **3 passed**. |
| High | Worker health, scheduler, metrics and dead-letter routes exposed operations data to ordinary users; dead-letter endpoints reported fake success. | `backend/app/routes/indexing.py` | Admin-only route assertions and unsupported-operation behavior; **3 passed**. |
| Critical | Refresh rotation was read-then-write and reuse revocation targeted one session row, while every rotation created a different session ID. | `backend/app/routes/auth.py`, `backend/app/database/repositories/session.py`, `backend/app/database/migrations/017_auth_session_families_sqlite.sql`, `backend/app/database/migrations/017_auth_session_families_postgres.sql` | `tests/test_refresh_auth.py`: concurrent refresh and family revocation; final combined targeted suites **22 passed**. |
| High | Access-token validation treated a missing `type` claim as `access` and did not reject absent subjects in the shared decoder. | `backend/app/services/auth.py` | `tests/test_auth_service.py`: missing access type and subject rejected; final combined targeted suites **22 passed**. |
| Medium | API docs overstated OAuth readiness and omitted indexing access rules and unsupported dead-letter behavior. | `docs/AUTHENTICATION_API.md` | Documentation review only; no separate automated test. |

## Outstanding findings

| Severity | Root cause / risk | Status |
| --- | --- | --- |
| Critical | OAuth callback uses provider user-info email to find/create/link a local account without requiring verified email or stable verified identity; authorization state is not PKCE-bound and redirect URIs are derived from issuer configuration. | Open. Do not claim OAuth/OIDC is secure or production-ready. |
| Critical | Crawler fetch follows redirects and does not validate each destination or resolved IP, allowing requests to private/loopback/link-local targets through an attacker-controlled URL or redirect. | Open. Add URL, DNS/IP and redirect validation plus egress restrictions and regression tests. |
| High | Browser persists long-lived refresh credentials in `localStorage`, exposing them to script injection. | Open. Move browser auth to secure HttpOnly cookies with CSRF protection and adapt the client; keep mobile credential storage platform-specific. |
| High | Upload reads the complete body before enforcing its 10 MiB limit and checks only filename extension. | Open. Stream bounded chunks and inspect file content before enqueueing. |
| High | No independent API-client identity or OAuth 2.0 client credentials implementation was found. | Open. User sessions must not serve as machine credentials. |
| High | `ProgressTracker` is process-local and jobs are not durably indexed by owner; multi-worker deployments can lose progress and cannot consistently authorize historical jobs. | Partially mitigated only for in-process records. Persist job ownership/state and query by owner in the database. |
| High | CSRF and cookie behavior, GraphQL resolver authorization/limits, broader document endpoints, API versioning, deployment secrets, and CI quality gates have not been validated end to end. | Open. |

## Test report

Executed on 2026-10-30 using the repository's Python 3.11 interpreter:

```text
pytest tests/test_auth.py tests/test_refresh_auth.py \
  tests/test_indexing_authorization.py tests/test_storage.py -q
22 passed, 27 warnings
```

Warnings include existing Pydantic/Strawberry deprecations and an unawaited
coroutine warning in `tests/conftest.py` database cleanup. No full test suite
or CI run was completed; no production readiness claim is made.

## Remaining deliverables

API-client tables/flow, OAuth/OIDC fixes, upload/crawler controls, GraphQL and
broader authorization coverage, migrations for additional identity models,
Postman assertions, CI integration, and a full security/CI report remain
unimplemented. Existing user data is preserved by the additive
`family_id` migration; current sessions are backfilled to their existing
`session_id` and are not invalidated by this migration.
