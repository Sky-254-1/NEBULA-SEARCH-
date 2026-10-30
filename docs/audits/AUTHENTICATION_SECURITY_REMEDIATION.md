# Authentication, Authorization, Security and QA Audit

**Audit date:** 2026-10-30  
**Scope inspected:** FastAPI authentication/session services, JWT validation,
indexing routes and workers, document ownership, OAuth callback, crawler fetch,
browser auth store, database migrations, existing tests and API documentation.

## Status

This is a partial remediation. The highest-priority indexing ownership and
refresh-token family defects listed below have fixes and focused test results.
The repository does not yet meet the brief's production acceptance criteria.
Working OAuth/OIDC, API-client credentials, organization tenancy, residual
crawler DNS-rebinding/egress controls, GraphQL authorization and production-
wide CI verification remain open.

## Inventory

| Area | Audit result |
| --- | --- |
| Password login and signup | Implemented; password hashes use PBKDF2-HMAC-SHA256 (200,000 rounds), brute-force throttling, and database-backed sessions. Reset and verification repositories/routes exist; delivery and end-to-end coverage need separate review. |
| JWT | HMAC signature, configured algorithm, issuer, audience, expiry and access token checks exist. This change now rejects missing subjects and missing access-token type claims. Key rotation and asymmetric key management are not implemented. |
| Refresh sessions | Hashed opaque tokens and session repository exist. Rotation was not atomic and reuse revocation did not cover descendants; fixed with a compare-and-set update, family identifier migration, and family-wide revocation. |
| OAuth/OIDC | Provider implementation is incomplete: settings and identity persistence are missing. Routes now fail closed with `501`; no provider login or account linking is available. |
| API clients | No separate client identity, secret lifecycle, scoped client credentials flow, or usage controls found in the inspected auth model. |
| Organizations | No tenant or organization model found. |
| Indexing authorization | Document ownership is checked before queue submission; job owner/document/status records are persisted and job reads/listing/cancellation are owner-filtered. Detailed progress remains process-local. |
| Operational routes | Worker health and scheduler were available to ordinary authenticated users; now administrator-gated. Metrics and dead-letter routes are also administrator-gated. |
| Dead-letter operations | Retry/list/delete were success-shaped placeholders. They now return explicit `501 Not Implemented`; a durable repository and actual retry workflow remain unimplemented. |
| Documents/uploads | Document reads/deletes use owner-filtered queries. Listing now uses owner-scoped SQL LIMIT/OFFSET and an independent count. Upload writes bounded chunks, enforces the limit while streaming, cleans up failed/interrupted files, applies a read timeout, and bounds DOCX entry count, expansion size, paths and compression ratios. Per-user storage quotas and full format validation remain open. |
| Crawler | Initial and redirected destinations now require HTTP(S) and resolve exclusively to public IPs; redirects are validated manually, and robots fetches do not follow redirects. DNS can still change between validation and connection, and network egress policy is not configured here. |
| Browser credentials | Browser refresh credentials are now held in HttpOnly cookies; the frontend clears legacy persisted refresh tokens and stores only short-lived access tokens. Mutating cookie-authenticated requests send a double-submit CSRF token, including requests that also carry a bearer header. Access tokens remain in `localStorage`, so script injection can still steal the short-lived access credential. |
| GraphQL, CI, infrastructure | Not fully audited or verified in this change. Existing tests cover selected API behavior, but no CI run or production deployment verification was performed. |

## Remediated findings

| Severity | Root cause | Changed files | Test added / actual result |
| --- | --- | --- | --- |
| Critical | Indexing start/reindex trusted document IDs and jobs were not associated with users; job lookup/cancel used globally keyed in-memory progress. | `backend/app/routes/indexing.py`, `backend/app/indexing/progress.py` | `tests/test_indexing_authorization.py`: cross-user document submission and job read/cancel denied; **3 passed**. |
| High | Worker health, scheduler, metrics and dead-letter routes exposed operations data to ordinary users; dead-letter endpoints reported fake success. | `backend/app/routes/indexing.py` | Admin-only route assertions and unsupported-operation behavior; **3 passed**. |
| Critical | Refresh rotation was read-then-write and reuse revocation targeted one session row, while every rotation created a different session ID. | `backend/app/routes/auth.py`, `backend/app/database/repositories/session.py`, `backend/app/database/migrations/017_auth_session_families_sqlite.sql`, `backend/app/database/migrations/017_auth_session_families_postgres.sql` | `tests/test_refresh_auth.py`: concurrent refresh and family revocation; final combined targeted suites **30 passed**. |
| High | Access-token validation treated a missing `type` claim as `access` and did not reject absent subjects in the shared decoder. | `backend/app/services/auth.py` | `tests/test_auth_service.py`: missing access type and subject rejected; final combined targeted suites **30 passed**. |
| Medium | API docs overstated OAuth readiness and omitted indexing access rules and unsupported dead-letter behavior. | `docs/AUTHENTICATION_API.md` | Documentation review only; no separate automated test. |
| Critical risk mitigated; feature unavailable | OAuth endpoints attempted email-based account linking without provider verification, while provider config referenced nonexistent settings and the identity table was missing. | `backend/app/routes/oauth.py`, `tests/test_oauth_fail_closed.py`, `docs/AUTHENTICATION_API.md` | Verified authorize/callback/link/unlink/accounts fail closed; unauthenticated linking returns `401`; `tests/test_oauth_fail_closed.py` passed. |
| Critical, partially mitigated | Crawler followed redirects automatically and never checked resolved destination addresses; robots.txt followed redirects too. | `backend/app/crawler/security.py`, `backend/app/crawler/crawler.py`, `backend/app/crawler/robots.py`, `tests/test_crawler_ssrf.py` | Private URL is blocked before robots lookup, private initial target blocked, public-to-loopback redirect blocked, public target works; `tests/test_crawler_ssrf.py`: **4 passed**. DNS rebinding and external egress policy remain open. |
| High, mitigated for supported upload formats | Upload buffered the entire body before checking size and trusted the file extension and client MIME. | `backend/app/routes/documents.py`, `tests/test_upload_validation.py` | Streaming limit, malformed text/PDF rejection, DOCX expansion bounds, timeout/interruption cleanup and generated storage names are covered. Latest upload + pagination run: **8 passed**. Per-user quotas and full MIME/content coverage remain open. |
| High, partially mitigated | Browser refresh tokens were persisted in localStorage, and cookie-authenticated mutations needed explicit CSRF integration. | `frontend/src/api/client.ts`, `frontend/src/api/base.js`, `frontend/src/state/useAuthStore.ts`, `frontend/src/context/AuthContext.tsx`, `frontend/src/auth/AuthContext.jsx`, `frontend/src/utils/storage.js`, browser mutation callers, `backend/app/middleware/security.py`, `backend/app/routes/mfa.py`, `backend/app/routes/webauthn.py` | `tests/test_csrf_cookie_auth.py`: bearer header cannot bypass CSRF when cookies are present; matching cookie/header is accepted. Latest focused security suite: **38 passed, 43 warnings**. Browser build was not run because `frontend/node_modules` is absent. |
| Medium | Document listing fetched a capped first batch, then sliced in application memory, causing inaccurate totals and inaccessible later pages. | `backend/app/database/repositories/document.py`, `backend/app/routes/documents.py`, `tests/test_document_pagination.py`, `docs/AUTHENTICATION_API.md` | Added stable owner-filtered SQL pagination and independent user count. Regression test seeds 61 documents for one user and 3 for another; **1 passed**. |
| High, partially mitigated | Upload failures could leave partial files; DOCX validation did not limit archive expansion or entries. | `backend/app/routes/documents.py`, `tests/test_upload_validation.py` | Added bounded archive checks, 60-second handler read timeout and cleanup on validation failure/cancellation. Oversize, malformed formats, path-like filename, archive expansion, timeout and interruption cases; upload + pagination suites **8 passed**. Per-user quota remains open. |
| High, partially mitigated | Indexing job ownership existed only in the process-local progress tracker; PostgreSQL had no corresponding `index_jobs` table. | `backend/app/database/migrations/018_index_job_ownership_sqlite.sql`, `backend/app/database/migrations/018_index_job_ownership_postgres.sql`, `backend/app/database/repositories/indexing_job.py`, `backend/app/routes/indexing.py`, `backend/app/indexing/tasks.py`, `backend/app/indexing/worker.py`, `tests/test_indexing_authorization.py` | Queue submissions now create owner-scoped durable job rows before enqueue, reads/listing/cancellation authorize against those records, and worker lifecycle status is persisted. Focused tests cover owner isolation and durable records; detailed progress still remains process-local. |

## Outstanding findings

| Severity | Root cause / risk | Status |
| --- | --- | --- |
| High | No verified OAuth/OIDC provider flow, identity persistence, PKCE/state binding, nonce validation, redirect allowlisting or explicit account-linking flow is implemented. The existing routes now return `501`. | Open. OAuth login and account linking are unavailable until implemented and verified. |
| High residual | DNS addresses are checked before each crawler request, but the HTTP client resolves the hostname again when connecting; DNS rebinding can race the check. No network egress policy is defined in this repository. | Partially mitigated. Pin resolved addresses during the request or enforce network-level egress restrictions. |
| Medium residual | Browser access tokens remain in `localStorage`, so script injection can steal the short-lived access credential. Refresh tokens are now cookie-backed and are not persisted by the frontend. | Partially mitigated. A cookie-only browser access-token migration would further reduce token exposure; retain platform-specific secure storage for mobile. |
| Medium residual | Upload streaming and basic content validation are implemented. DOCX archive expansion limits and comprehensive MIME/content validation need additional hardening. | Partially mitigated; broader malicious archive/type tests remain open. |
| High | No independent API-client identity or OAuth 2.0 client credentials implementation was found. | Open. User sessions must not serve as machine credentials. |
| Medium residual | Detailed progress, ETA, chunk counts, and worker assignment remain in `ProgressTracker`, which is process-local; the durable job table currently stores owner and lifecycle status. | Partially mitigated. Persist detailed progress and make queue ownership/state consistent across workers. |
| High | CSRF and cookie behavior, GraphQL resolver authorization/limits, broader document endpoints, API versioning, deployment secrets, and CI quality gates have not been validated end to end. | Open. |

## Test report

Executed on 2026-10-30 using the repository's Python 3.11 interpreter:

```text
pytest tests/test_auth.py tests/test_auth_service.py tests/test_refresh_auth.py \
  tests/test_indexing_authorization.py tests/test_storage.py \
  tests/test_oauth_fail_closed.py tests/test_crawler_ssrf.py \
  tests/test_upload_validation.py tests/test_csrf_cookie_auth.py \
  tests/test_document_pagination.py -q --show-capture=no
38 passed, 43 warnings
```

Warnings include existing Pydantic/Strawberry deprecations and an unawaited
coroutine warning in `tests/conftest.py` database cleanup. The latest focused
security suite passed **38 tests**. A root-wide `pytest -q` attempt stopped at
collection with **72 errors**, including nested-checkout imports, binary `.txt`
output artifacts collected as tests, and a pre-existing untracked backend test
that fails during import. A second run restricted to `tests/` completed with
**149 passed, 6 failed, 16 errors**: live-server E2E tests could not connect to
localhost and two search tests use stale call signatures. No frontend build or
CI run was completed; no production readiness claim is made.

## Remaining deliverables

API-client tables/flow, OAuth/OIDC fixes, upload/crawler controls, GraphQL and
broader authorization coverage, migrations for additional identity models,
Postman assertions, CI integration, and a full security/CI report remain
unimplemented. Existing user data is preserved by the additive
`family_id` migration; current sessions are backfilled to their existing
`session_id` and are not invalidated by this migration.
