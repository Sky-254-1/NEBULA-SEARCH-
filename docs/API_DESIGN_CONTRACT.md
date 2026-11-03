# API design contract

## Routes and versions

The application version is reported as `1.1.0`. URI versions are separate:
`/api/v1` remains available (with deprecation headers) and `/api/v2` currently
contains the newer search routes. Version 2 is not a wholesale replacement for
all v1 resource routes. OpenAPI reports both facts and marks authentication per
operation instead of applying bearer authentication globally.

The canonical browser API base is the server origin. The TypeScript API client
accepts shorthand v1 paths such as `/documents/`, shorthand v2 paths such as
`/v2/search/`, and fully qualified `/api/v1/...` or `/api/v2/...` paths. It
resolves each to exactly one versioned route.

## Responses and errors

Successful responses retain their route-specific typed shapes for compatibility.
Errors use one envelope:

```json
{
  "status": "error",
  "error_code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "validation_errors": [{"field": "page", "message": "Input should be greater than or equal to 1"}],
  "request_id": "...",
  "timestamp": 0
}
```

Internal failures return a safe message. The same request ID appears in the
`X-Request-ID` header and error body. OpenAPI includes the `APIError` schema and
describes default errors for API operations.

## Pagination

List responses use `page` (one-based), `page_size`, and a `pagination` object
containing `total`, `page`, `page_size`, `total_pages`, `has_next`, and
`has_previous`. Empty collections have `total_pages: 0`; an out-of-range page
returns an empty item list and accurate `has_previous`/`has_next` values.
Document, legacy storage-document, notification, indexing-job, and search list
routes preserve their existing top-level fields and add or return this metadata.

Search providers do not expose a common exact global result count. Search
`total` therefore describes the ranked matching candidate set retrieved for
the request, with a lookahead item used to determine `has_next`; it is not a
provider-wide corpus count.

## Indexing jobs

New clients should create jobs with `POST /api/v1/indexing/jobs`, inspect them
with `GET /api/v1/indexing/jobs/{job_id}`, and use the cancel/retry subroutes.
Creation returns `202 Accepted` and a `Location` header. The existing `/start`,
`/job/{job_id}`, `/cancel/{job_id}`, and `/retry/{job_id}` routes remain for
older clients. Job list data remains under `data.jobs` and includes pagination
metadata. Access remains owner-scoped on both old and new routes.
