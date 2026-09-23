# Phase 1 — State of the Project Audit
**Date:** 2026-07-29  
**Base commit:** cca905d (main)  
**Auditor:** Automated investigation (no code changes in this phase)  

---

## 1. Dependency Health

### Python (35 outdated packages)
Key outdated packages:
- `fastapi` 0.135.1 → 0.140.13 (minor feature release)
- `pydantic` 2.12.5 → 2.13.4 (patch, includes security fixes)
- `uvicorn` 0.41.0 → 0.52.0 (minor feature release)
- `mypy` 1.20.2 → 2.3.0 (major version bump — would require type-fix migration)
- `redis` 5.3.1 → 8.0.1 (major version bump — breaking changes likely)
- `pytest` 9.1.0 → 9.1.1 (patch)
- `ruff` 0.15.22 → 0.16.0 (minor)

### Node/Frontend (17 outdated packages)
Key outdated:
- `react` 19.2.7 → 19.2.8, `react-dom` 19.2.7 → 19.2.8 (patches)
- `@vitejs/plugin-react` 4.7.0 → 6.0.4 (major — likely Vite 6 migration)
- `react-router-dom` 6.30.4 → 7.18.2 (major — breaking changes)
- `eslint` 9.39.5 → 10.8.0 (major)
- `framer-motion` 11.18.2 → 12.43.0 (major)

### Security Vulnerabilities
- `pip-audit` not installed locally (unavailable in current environment)
- **GitHub Dependabot** reports 9 vulnerabilities on default branch:
  - 1 critical, 1 high, 7 moderate
  - Details: https://github.com/Sky-254-1/Nebula-search-engine-/security/dependabot

### Assessment
Most Python packages are patch/minor behind. The major-version outliers (`mypy`, `redis`, `@vitejs/plugin-react`, `react-router-dom`, `eslint`, `framer-motion`) would require migration work, not just `pip install --upgrade`. **No critical/high CVEs confirmed locally** — Dependabot alerts should be reviewed by a human.

---

## 2. Full mypy Error Inventory

**Current count:** 237 errors in 75 files (checked 181 source files)  
**Baseline trend:** 243 → 237 → 235 → 233 → 234 → 237 — oscillating, not converging

### Category Breakdown
| Category | Count | Root cause |
|---|---|---|
| `missing_attribute` | 99 | Optional vector DB clients (qdrant, milvus, pgvector, elasticsearch) not installed → `None.has no attribute` |
| `other` | 69 | Scattered; requires per-file inspection |
| `arg_mismatch` | 30 | Function argument type mismatches |
| `assignment_mismatch` | 24 | Variable assignment type mismatches |
| `return_mismatch` | 11 | Return type mismatches |
| `unsupported_operand` | 4 | Arithmetic on incompatible types |

### Root Cause Analysis
1. **99 `missing_attribute` errors**: These are **noise from uninstalled optional dependencies**. The vector store backends (`qdrant_store.py`, `milvus_store.py`, `pgvector_store.py`, `elasticsearch_store.py`) import optional clients that aren't in `requirements.txt`. mypy infers `None` and flags every method call. These won't resolve without either installing those packages or adding proper `TYPE_CHECKING` guards.
2. **11 `return_mismatch`**: Genuine annotation bugs. Example: `collection.py` and `bookmark.py` `create()` declared `-> int` but return `None` on empty rows.
3. **30 `arg_mismatch` + 24 `assignment_mismatch`**: Real type issues, likely pre-existing dynamic typing patterns that mypy is now catching.
4. **69 `other`**: Needs per-file triage.

### Oscillation Explanation
The count oscillates because fixing one mismatch (e.g., changing `-> int` to `-> int | None`) removes that error but may expose a new mismatch at the call site. Without a systematic, category-by-category approach, the count creeps up and down.

### Recommendation
Stop chasing the count. Fix one category at a time with full test suite validation per commit. The 99 optional-dependency errors should be addressed first with `TYPE_CHECKING` guards or stub files, which will immediately drop the count and make the remaining 138 errors manageable.

---

## 3. Full Test Coverage Report

### Backend (pytest --cov)
**Overall:** 49% (8052 missed statements / 15908 total)

#### Files Under 40% Coverage
| File | Coverage | Missing Lines |
|---|---|---|
| `backend/app/database/repositories/entities.py` | 0% | 4-93 |
| `backend/app/database/repositories/search_history.py` | 0% | 3-95 |
| `backend/app/database/repositories/synonyms.py` | 0% | 4-70 |
| `backend/app/health_routes.py` | 15% | 16, 29, 42-109, 118-185 |
| `backend/app/crawler/crawler.py` | 24% | 36-45, 49-95, 107, 138-294 |
| `backend/app/database/repositories/bookmark.py` | 23% | 5, 8-12, 15-24, 27-35, 38-50, 53-57, 60-65 |
| `backend/app/database/repositories/collection.py` | 29% | 5, 8-12, 15, 22-32, 35-47, 50-52, 55-59, 62, 68-69 |
| `backend/app/database/repositories/notification.py` | 29% | 9, 20-31, 35-46, 49-54, 57-63, 66-72, 75-81 |
| `backend/app/database/repositories/document.py` | 32% | 10, 19-28, 31-37, 40, 48-53, 56-67, 76-80, 83-88, 92-93 |
| `backend/app/database/repositories/autocomplete.py` | 48% | 18-35, 39-52, 56-60, 64-74, 89-94, 125-129 |
| `backend/app/database/repositories/suggestion_repository.py` | 34% | 13, 21-36, 42-53, 58-112, 122-133, 139-149, 155-165, 169-173, 183-194, 200-210, 214-224, 229-258, 275-292, 298-309, 313-322, 330-338, 348-361, 365-377 |
| `backend/app/database/repositories/settings.py` | 28% | 11, 14-20, 23-39 |
| `backend/app/database/repositories/audit.py` | 40% | 59-81, 85, 92, 99, 106, 113-127, 136-143, 147-186 |
| `backend/app/crawler/robots.py` | 34% | 26-39, 42-53, 56-68, 71 |
| `backend/app/hybrid/filters.py` | 30% | 48, 68, 71-83, 103, 109, 119-166, 191-202, 210-219, 227-236, 244, 252-255, 264-287, 299-328 |
| `backend/app/hybrid/dedupe.py` | 47% | 65, 93, 96, 109, 133-143, 172-209, 226-260, 264-269 |
| `backend/app/database/repositories/spell.py` | 36% | 24-25, 34-35, 39-68, 72-78, 82-89, 93-98, 102-105, 109-113 |

### Frontend (vitest --coverage)
Not run in this phase — will be measured in Phase 2.

---

## 4. Router Mount Audit

**Result:** 2 router files exist but are **NOT mounted** in `backend/app/main.py`.

| Unmounted File | Purpose | Risk |
|---|---|---|
| `backend/app/routes/mfa.py` | Multi-factor authentication routes | **HIGH** — MFA is documented and tested, but routes are unreachable |
| `backend/app/routes/oauth.py` | OAuth provider routes | **MEDIUM** — OAuth integration partially implemented |

This is the **same class of bug** that previously occurred with the MFA router (noted in project history).

### Code Reference
`backend/app/main.py` includes 27 `app.include_router(...)` calls. The two files above define routers with `APIRouter` instances that are never referenced.

### Assessment
- `mfa.py`: **Needs human decision** — MFA is enforced in auth flow (`app/services/auth.py`), but the router endpoints for setup/management are unreachable. Either mount the router or remove the file to avoid confusion.
- `oauth.py`: Similar — OAuth providers are partially implemented but the routes are unreachable.

---

## 5. Migration Diff Audit (Postgres vs SQLite)

### Files Checked
| Migration | Postgres File | SQLite File | Parity |
|---|---|---|---|
| 001 | `001_initial_schema_postgres.sql` | `001_initial_schema_sqlite.sql` | ✅ |
| 002 | `002_add_users_postgres.sql` | `002_add_users_sqlite.sql` | ✅ |
| 003 | `003_postgres.sql` | `003_sqlite.sql` | ✅ (parity fix already applied in cca905d) |
| 004 | `004_indexes_constraints.sql` | `004_indexes_constraints_sqlite.sql` | ✅ |
| 005+ | Various | Various | ✅ |

### Assessment
No schema-parity gaps found beyond the one already fixed in migration 003. Both `database/migrations/` and `database/schema/` are consistent.

---

## 6. Migration Idempotency Status

### Approach Used
- **Tracking table**: `migrations` table with `id` + `name` + `applied_at`
- **Safe patterns**: `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`

### Files Reviewed
All migration files in `database/migrations/` and `database/schema/` use idempotent patterns. The migration runner (`backend/app/database/migrate.py`) checks the tracking table before applying.

### Assessment
Idempotency is correctly implemented. No gaps found.

---

## 7. Docs vs Reality Audit

### Documented Features That Exist in Code
- Full-text search with BM25, vector search, hybrid fusion ✅
- AI chat with streaming ✅
- MFA enforcement ✅
- Document upload and management ✅
- Webhooks ✅
- Notifications ✅
- Saved searches, bookmarks, collections ✅
- Incremental re-indexing ✅
- Spell correction ✅
- Autocomplete ✅
- Search suggestions ✅
- Analytics dashboard ✅
- Recommendations ✅

### Documented Features That Are Stale or Missing
| Doc Reference | Issue |
|---|---|
| `docs/ux/visual-specifications/main-app/05_Document_Upload.md` | Describes upload flow that exists, but no screenshots of actual current UI |
| `README.md` setup instructions | Do not mention the WebKit install issue or Playwright browser setup |
| `docs/CI_CD_PIPELINE.md` | Does not mention WebKit install step (this was just added in fix/playwright-webkit-install) |
| `CHANGELOG.md` | Last entry predates cca905d — does not document the critical fixes from that commit |

### Assessment
Documentation is broadly accurate but has gaps in setup instructions and changelog maintenance.

---

## 8. Security Pass

### Secrets Scanning
- `gitleaks` not installed locally — cannot run automated scan
- Manual review of recent commits (cca905d and earlier) shows:
  - Test passwords changed to 8+ chars in cca905d ✅
  - No hardcoded API keys in recent diffs
  - `.env.example` contains only placeholder values ✅
  - `.env.production` exists but is gitignored ✅

### Dependency Vulnerabilities
- GitHub Dependabot: 1 critical, 1 high, 7 moderate (details at https://github.com/Sky-254-1/Nebula-search-engine-/security/dependabot)
- `pip-audit` unavailable locally — **needs human review of Dependabot alerts**

### CORS/Auth Config
- `backend/app/middleware/security.py`: CORS configured with explicit allowlist — needs verification against production domains
- `backend/app/config.py`: Default `CORS_ORIGINS` includes `*` in some code paths — **needs human confirmation this is overridden in production**
- JWT secret in `.env.example` is a placeholder — good ✅
- Test JWT secrets in CI are 32+ chars — good ✅

### Assessment
No immediate hardcoded secrets found. Dependabot alerts and CORS defaults need human review before production release.

---

## Summary: What Needs Human Decision

1. **2 unmounted routers** (`mfa.py`, `oauth.py`) — mount them or remove the files
2. **Dependabot alerts** — 1 critical, 1 high, 7 moderate need review
3. **CORS config** — confirm `*` wildcard is never used in production paths
4. **mypy** — 237 errors, oscillation pattern identified, safe fix strategy proposed
5. **pip-audit** — not installed, needs to be run in CI or locally with proper Python environment

## Summary: What Phase 2 Will Fix

1. Coverage gaps on files under 40% (13 files listed above)
2. mypy errors — category-by-category, one commit per category
3. WebKit Playwright install for CI
4. Integration tests for migration idempotency and router mount verification
5. Full E2E suite on all configured browsers/projects