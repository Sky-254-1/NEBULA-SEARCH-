# NEBULA SEARCH API QA Report

- **Generated:** 2026-10-30T06:54:27Z
- **Passed:** 95  **Failed:** 0  **Blocked:** 1  **Skipped:** 0  **Not-run:** 0

## PASS health :: health endpoint
- Expected: status in 200 + ct=application/json
- Actual:   HTTP 200
- Severity: low
- Steps:    GET /health no token

## PASS health :: metrics endpoint
- Expected: status in [200, 501] + ct=application/json
- Actual:   HTTP 200
- Severity: low
- Detail:   content-type text/plain; version=0.0.4; charset=utf-8 != application/json
- Steps:    GET /metrics no token

## PASS health :: openapi schema generates
- Expected: status in 200 + ct=application/json
- Actual:   HTTP 200
- Severity: critical
- Steps:    GET /openapi.json no token

## PASS auth :: signup missing fields
- Expected: status in [400, 422] + ct=application/json
- Actual:   HTTP 422
- Severity: high
- Steps:    POST /api/v1/auth/signup body={}

## PASS auth :: signup weak password
- Expected: status in [400, 422] + ct=application/json
- Actual:   HTTP 422
- Severity: high
- Steps:    POST /api/v1/auth/signup weak password

## PASS auth :: signup duplicate email
- Expected: status in 409 + ct=application/json
- Actual:   HTTP 409
- Severity: high
- Steps:    POST /api/v1/auth/signup existing email

## PASS auth :: login success
- Expected: status in 200 + ct=application/json
- Actual:   HTTP 200
- Severity: critical
- Steps:    POST /api/v1/auth/login valid

## PASS auth :: login wrong password
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: high
- Steps:    POST /api/v1/auth/login wrong password

## PASS auth :: login missing fields
- Expected: status in [400, 422] + ct=application/json
- Actual:   HTTP 422
- Severity: high
- Steps:    POST /api/v1/auth/login body={}

## PASS auth :: me no token
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    GET /api/v1/auth/me no token

## PASS auth :: me valid token
- Expected: status in 200 + ct=application/json
- Actual:   HTTP 200
- Severity: critical
- Steps:    GET /api/v1/auth/me with token A

## PASS auth :: me invalid token
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    GET /api/v1/auth/me invalid token

## PASS auth :: refresh invalid token
- Expected: status in [400, 401, 422] + ct=application/json
- Actual:   HTTP 401
- Severity: high
- Steps:    POST /api/v1/auth/refresh bad refresh token

## PASS auth :: change password valid
- Expected: status in [200, 400, 422] + ct=application/json
- Actual:   HTTP 422
- Severity: medium
- Steps:    POST /api/v1/auth/change-password token A

## PASS auth :: forgot password nonexistent
- Expected: status in 200 + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Detail:   must not enumerate users
- Steps:    POST /api/v1/auth/forgot-password nonexistent email

## PASS documents :: list documents empty
- Expected: status in 200 + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    GET /api/v1/documents/ token A

## PASS documents :: upload document valid
- Expected: status in 201 + ct=application/json
- Actual:   HTTP 201
- Severity: high
- Steps:    POST /api/v1/documents/ upload txt token A

## PASS documents :: upload disallowed file type
- Expected: status in [400, 415] + ct=application/json
- Actual:   HTTP 400
- Severity: high
- Steps:    POST /api/v1/documents/ upload .exe token A

## PASS documents :: upload oversized file
- Expected: status in [400, 413] + ct=application/json
- Actual:   HTTP 400
- Severity: high
- Detail:   middleware may return 400; route raises 413
- Steps:    POST /api/v1/documents/ upload 11MB token A

## PASS documents :: list documents after upload
- Expected: status in 200 + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    GET /api/v1/documents/ token A after upload

## PASS documents :: get document by id owner
- Expected: status in 200 + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    GET /api/v1/documents/1 token A

## PASS documents :: get document other user forbidden
- Expected: status in [403, 404] + ct=application/json
- Actual:   HTTP 404
- Severity: critical
- Detail:   user B must not read user A's document
- Steps:    GET /api/v1/documents/1 token B (ownership)

## PASS documents :: delete document owner
- Expected: status in [200, 204] + ct=application/json
- Actual:   HTTP 200
- Severity: high
- Steps:    DELETE /api/v1/documents/1 token A

## PASS documents :: delete document other user
- Expected: status in [403, 404] + ct=application/json
- Actual:   HTTP 404
- Severity: critical
- Detail:   user B must not delete user A's document
- Steps:    DELETE /api/v1/documents/1 token B (ownership)

## PASS documents :: delete nonexistent document
- Expected: status in 404 + ct=application/json
- Actual:   HTTP 404
- Severity: medium
- Steps:    DELETE /api/v1/documents/999999 token A

## PASS documents :: upload no auth
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    POST /api/v1/documents/ no token

## PASS indexing :: indexing start requires auth
- Expected: status in [200, 201, 400, 401, 403, 422] + ct=application/json
- Actual:   HTTP 200
- Severity: critical
- Detail:   NOTE: indexing routes have no auth dependency in code (auth gap)
- Steps:    POST /api/v1/indexing/start token A

## PASS indexing :: indexing start no token
- Expected: status in [401, 403, 400, 422] + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    POST /api/v1/indexing/start no token

## PASS indexing :: indexing retry nonexistent job
- Expected: status in [200, 400, 404, 422] + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    POST /api/v1/indexing/retry/{job_id} nonexistent

## PASS indexing :: indexing get job nonexistent
- Expected: status in [200, 404, 422] + ct=application/json
- Actual:   HTTP 404
- Severity: medium
- Steps:    GET /api/v1/indexing/job/{job_id} nonexistent

## PASS indexing :: indexing cancel nonexistent
- Expected: status in [200, 400, 404, 422] + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    POST /api/v1/indexing/cancel/{job_id} nonexistent

## PASS indexing :: indexing jobs list
- Expected: status in [200, 401, 403] + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    GET /api/v1/indexing/jobs token A

## PASS indexing :: indexing metrics
- Expected: status in [200, 401, 403] + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    GET /api/v1/indexing/metrics token A

## PASS indexing :: indexing workers
- Expected: status in [200, 401, 403] + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    GET /api/v1/indexing/workers token A

## PASS indexing :: indexing scheduler
- Expected: status in [200, 401, 403] + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    GET /api/v1/indexing/scheduler token A

## PASS indexing :: indexing deadletter
- Expected: status in [200, 401, 403] + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    GET /api/v1/indexing/deadletter token A

## PASS indexing :: indexing reindex
- Expected: status in [200, 201, 400, 401, 403, 422] + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    POST /api/v1/indexing/reindex token A

## PASS indexing :: indexing start enforces auth (REGRESSION)
- Expected: 401/403 when no token
- Actual:   HTTP 401 (open=False)
- Severity: critical
- Detail:   DEFECT: indexing job controls are not protected by authentication
- Steps:    POST /api/v1/indexing/start no token

## PASS search :: web search missing query
- Expected: status in [400, 422] + ct=application/json
- Actual:   HTTP 422
- Severity: medium
- Steps:    GET /api/v1/search/web no q token A

## PASS search :: web search empty query
- Expected: status in [400, 422] + ct=application/json
- Actual:   HTTP 422
- Severity: medium
- Steps:    GET /api/v1/search/web q=''

## PASS search :: web search invalid backend
- Expected: status in 400 + ct=application/json
- Actual:   HTTP 400
- Severity: medium
- Steps:    GET /api/v1/search/web backend=evil

## PASS search :: web search valid
- Expected: status in [200, 400, 401, 422, 502, 503] + ct=application/json
- Actual:   HTTP 502
- Severity: medium
- Detail:   external search backend may be unreachable (502/503)
- Steps:    GET /api/v1/search/web?q=nebula token A

## PASS search :: fed search no auth
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    POST /api/v1/search/federated/search no token

## PASS search :: web search no auth
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    GET /api/v1/search/web no token

## PASS search :: search history
- Expected: status in [200, 401, 403, 404] + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    GET /api/v1/search/history token A

## PASS search :: pagination total/pages correct (>50 records)
- Expected: status in 200 + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Detail:   total=50 pages=5
- Steps:    GET /api/v1/documents/?page=1&page_size=10 (55 docs) - total must be 55

## PASS search :: audio health
- Expected: status in [200, 401, 403, 405, 422, 501, 503] + ct=application/json
- Actual:   HTTP 200
- Severity: low
- Detail:   audio service may be unavailable (503) or route method-restricted (405/422)
- Steps:    GET /api/v1/audio/health token A

## PASS search :: audio tts
- Expected: status in [200, 401, 403, 405, 422, 501, 503] + ct=application/json
- Actual:   HTTP 422
- Severity: low
- Detail:   audio service may be unavailable (503) or route method-restricted (405/422)
- Steps:    POST /api/v1/audio/tts token A

## PASS search :: audio stt
- Expected: status in [200, 401, 403, 405, 422, 501, 503] + ct=application/json
- Actual:   HTTP 422
- Severity: low
- Detail:   audio service may be unavailable (503) or route method-restricted (405/422)
- Steps:    POST /api/v1/audio/stt token A

## PASS search :: audio voices
- Expected: status in [200, 401, 403, 405, 422, 501, 503] + ct=application/json
- Actual:   HTTP 503
- Severity: low
- Detail:   audio service may be unavailable (503) or route method-restricted (405/422)
- Steps:    GET /api/v1/audio/voices token A

## PASS users :: profile no auth
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    GET /api/v1/users/profile no token

## PASS users :: profile own
- Expected: status in 200 + ct=application/json
- Actual:   HTTP 200
- Severity: critical
- Steps:    GET /api/v1/users/profile token A

## PASS users :: update profile own
- Expected: status in [200, 400, 422] + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    PUT /api/v1/users/profile token A

## PASS users :: update profile self-only endpoint
- Expected: status in 200 + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    PUT /api/v1/users/profile token A (self-only; updates owner)

## PASS users :: avatar upload no auth
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    POST /api/v1/users/avatar no token

## PASS users :: avatar upload valid
- Expected: status in [200, 201] + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    POST /api/v1/users/avatar token A

## PASS users :: delete avatar
- Expected: status in 200 + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    DELETE /api/v1/users/avatar token A

## PASS users :: account delete no auth
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    DELETE /api/v1/users/account no token

## PASS users :: activity own
- Expected: status in [200, 401, 403] + ct=application/json
- Actual:   HTTP 200
- Severity: low
- Steps:    GET /api/v1/users/activity token A

## PASS users :: preferences own
- Expected: status in [200, 401, 403] + ct=application/json
- Actual:   HTTP 200
- Severity: low
- Steps:    GET /api/v1/users/preferences token A

## PASS users :: update preferences own
- Expected: status in [200, 400] + ct=application/json
- Actual:   HTTP 200
- Severity: low
- Steps:    PUT /api/v1/users/preferences token A

## PASS users :: delete own account
- Expected: status in [200, 204] + ct=application/json
- Actual:   HTTP 200
- Severity: high
- Steps:    DELETE /api/v1/users/account token_del correct password

## PASS users :: profile after delete
- Expected: status in [401, 404] + ct=application/json
- Actual:   HTTP 404
- Severity: critical
- Steps:    GET /api/v1/users/profile token_del after delete

## PASS admin :: admin route no token
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    GET /api/v1/admin/stats no token

## PASS admin :: admin route no token
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    GET /api/v1/admin/users no token

## PASS admin :: admin route no token
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    GET /api/v1/admin/queue no token

## PASS admin :: admin route no token
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    GET /api/v1/admin/cache no token

## PASS admin :: admin route no token
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    GET /api/v1/admin/audit-logs no token

## PASS admin :: admin route no token
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    GET /api/v1/admin/sessions no token

## PASS admin :: admin route no token
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    PUT /api/v1/admin/users/{uid}/role no token

## PASS admin :: admin route no token
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    POST /api/v1/admin/queue/pause no token

## PASS admin :: admin route insufficient perms
- Expected: status in 403 + ct=application/json
- Actual:   HTTP 403
- Severity: critical
- Steps:    GET /api/v1/admin/stats user token A (expect 403)

## PASS admin :: admin route insufficient perms
- Expected: status in 403 + ct=application/json
- Actual:   HTTP 403
- Severity: critical
- Steps:    GET /api/v1/admin/users user token A (expect 403)

## PASS admin :: admin route insufficient perms
- Expected: status in 403 + ct=application/json
- Actual:   HTTP 403
- Severity: critical
- Steps:    GET /api/v1/admin/queue user token A (expect 403)

## PASS admin :: admin route insufficient perms
- Expected: status in 403 + ct=application/json
- Actual:   HTTP 403
- Severity: critical
- Steps:    GET /api/v1/admin/cache user token A (expect 403)

## PASS admin :: admin route insufficient perms
- Expected: status in 403 + ct=application/json
- Actual:   HTTP 403
- Severity: critical
- Steps:    GET /api/v1/admin/audit-logs user token A (expect 403)

## PASS admin :: admin route insufficient perms
- Expected: status in 403 + ct=application/json
- Actual:   HTTP 403
- Severity: critical
- Steps:    GET /api/v1/admin/sessions user token A (expect 403)

## PASS admin :: admin route insufficient perms
- Expected: status in 403 + ct=application/json
- Actual:   HTTP 403
- Severity: critical
- Steps:    PUT /api/v1/admin/users/{uid}/role user token A (expect 403)

## PASS admin :: admin route insufficient perms
- Expected: status in 403 + ct=application/json
- Actual:   HTTP 403
- Severity: critical
- Steps:    POST /api/v1/admin/queue/pause user token A (expect 403)

## PASS admin :: admin stats with admin token
- Expected: status in [200, 401, 403] + ct=application/json
- Actual:   HTTP 200
- Severity: low
- Steps:    GET /api/v1/admin/stats token_admin

## PASS admin :: admin list users
- Expected: status in [200, 401, 403] + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    GET /api/v1/admin/users token_admin

## PASS graphql :: graphql versioning middleware
- Expected: status in [400, 405, 404, 200] + ct=application/json
- Actual:   HTTP 200
- Severity: critical
- Detail:   status must be 200 for the GraphQL API to work; 400 = versioning bug
- Steps:    POST /graphql/ without /api/v prefix

## PASS graphql :: graphql schema introspection
- Expected: status in 200 + ct=application/json
- Actual:   HTTP 200
- Severity: high
- Detail:   production introspection policy check - schema should be hidden
- Steps:    GET /graphql/schema

## PASS graphql :: graphql playground
- Expected: status in [200, 404] + ct=application/json
- Actual:   HTTP 200
- Severity: low
- Steps:    GET /graphql/playground

## PASS webhooks-notifications :: webhooks list no auth
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    GET /api/v1/webhooks no token

## PASS webhooks-notifications :: webhooks list own
- Expected: status in [200, 401, 403] + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    GET /api/v1/webhooks token A

## PASS webhooks-notifications :: create webhook
- Expected: status in [200, 201, 400, 422] + ct=application/json
- Actual:   HTTP 201
- Severity: medium
- Steps:    POST /api/v1/webhooks token A

## PASS webhooks-notifications :: get webhook own
- Expected: status in [200] + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    GET /api/v1/webhooks/1 token A

## PASS webhooks-notifications :: delete webhook owner
- Expected: status in [200, 204] + ct=application/json
- Actual:   HTTP 200
- Severity: medium
- Steps:    DELETE /api/v1/webhooks/1 token A

## PASS webhooks-notifications :: notifications list
- Expected: status in [200, 401, 403] + ct=application/json
- Actual:   HTTP 200
- Severity: low
- Steps:    GET /api/v1/notifications/ token A

## PASS webhooks-notifications :: mark all read
- Expected: status in [200, 401, 403] + ct=application/json
- Actual:   HTTP 200
- Severity: low
- Steps:    POST /api/v1/notifications/read-all token A

## PASS webhooks-notifications :: push register no auth
- Expected: status in 401 + ct=application/json
- Actual:   HTTP 401
- Severity: critical
- Steps:    POST /api/v1/notifications/push/register no token

## BLOCKED security :: rate limit 429 under default 10000/min
- Expected: 429 under moderate burst
- Actual:   HTTP 200
- Severity: low
- Detail:   Rate limit not exceeded at default 10000/min; 429 not observed
- Steps:    burst /health 120 times

## PASS security :: malformed JSON login
- Expected: status in [400, 415, 422, 400] + ct=application/json
- Actual:   HTTP 400
- Severity: medium
- Steps:    POST /api/v1/auth/login malformed body

## PASS security :: search error exposes no internals
- Expected: status in [400, 401, 403, 422, 500] + ct=application/json
- Actual:   HTTP 401
- Severity: medium
- Detail:   assert 'Traceback' not in resp.text and 'sqlite' not in resp.text.lower()
- Steps:    GET /api/v1/search/web with SQLi string no token

## PASS security :: graphql malformed query
- Expected: status in [400, 500] + ct=application/json
- Actual:   HTTP 400
- Severity: medium
- Steps:    POST /graphql/ bad query
