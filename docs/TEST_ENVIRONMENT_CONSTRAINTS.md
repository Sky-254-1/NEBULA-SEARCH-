# Test Environment Constraints

Known limitations of the local Windows test environment and how to work
around them without weakening the product's security posture.

Related: [TESTING_STRATEGY.md](TESTING_STRATEGY.md), [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## 1. Windows Application Control blocks SQLAlchemy's Cython DLL

### Symptom

```
ImportError: DLL load failed while importing _collections_cy:
An Application Control policy has blocked this file.
```

The file is
`...\site-packages\sqlalchemy\util\_collections_cy.cp3xx-win_amd64.pyd`.

### Cause

SQLAlchemy 2.x ships compiled Cython helpers for performance. On Windows,
[WDAC / AppLocker](https://learn.microsoft.com/windows/security/application-security/application-control/)
policies can block a DLL from loading when it lives outside an approved
path (typically the per-user `%LOCALAPPDATA%\Programs\Python` tree).

This is a host security policy. It is **not** something the repository can
or should bypass: do not disable the policy, rename the DLL, or copy it to
an allow-listed directory to make tests pass.

### Impact

SQLAlchemy 2.1 imports every Cython module eagerly in
`sqlalchemy/util/_has_cython.py`, so a blocked DLL prevents `import
sqlalchemy` from succeeding — and with it the whole backend test suite.

### Workarounds

* **Run the suite where the policy does not apply.** The authoritative runs
  are Linux CI (`.github/workflows/`) and Docker (`docker compose`), where
  the wheel loads normally.
* **Use a policy-compatible interpreter.** Install Python/SQLAlchemy under a
  path approved by the WDAC policy (for example a machine-wide
  `C:\Program Files\Python3xx`) and re-run the tests.
* **No pure-Python switch exists for SQLAlchemy 2.x.** (The old
  `DISABLE_SQLALCHEMY_CEXT` variable only affects source builds of 1.4.)

### Verify on a healthy host

```powershell
python -c "from sqlalchemy.util import _has_cython; print(_has_cython.HAS_CYEXTENSION)"
# True  -> Cython extensions loaded
# False -> pure-Python fallback in use
```

---

## 2. External search API keys are not configured

`BRAVE_API_KEY` and `SERPAPI_KEY` are **optional** paid backends. The default
`wikipedia` backend requires no credentials, so the core suite runs without
them.

* Backend unit tests never call the paid providers (they are mocked/patched).
* Backend E2E tests (`backend/tests/e2e/`) use `wikipedia` and mock the
  network.
* Playwright's `tests/e2e/search/search-web.spec.ts` already skips itself
  when both variables are unset:

  ```ts
  test.skip(!process.env.BRAVE_API_KEY && !process.env.SERPAPI_KEY, ...)
  ```

To exercise the paid backends locally, export the keys in the shell (never
commit them; `.env*` files are ignored). Unset keys must never be treated as
a test failure.

---

## 3. API endpoint drift

E2E specs and the frontend client target the versioned API surface:

| Area | Canonical prefix | Notes |
|------|------------------|-------|
| Search (v1) | `/api/v1/search/*` | `orchestrate`, `web`, `suggestions`, `history`, `save`, `saved` |
| Search (v2) | `/api/v2/search/*` | `autocomplete`, `spell-check`, `trending`, `popular`, `suggest`, `profile`, `analytics` |
| Documents | `/api/v1/documents/` | current; `/api/v1/storage/documents` remains as a legacy alias |
| Vector | `/api/v1/vector/*` | `documents/{id}/status`, `documents/{id}/index-now`, `search`, `ask` |
| AI | `/api/v1/ai/*` | `ask`, `ask/stream`, `chat/history` |
| Auth | `/api/v1/auth/*` | `signup`, `login`, `refresh`, `logout`, `me` |

If a spec references a path outside this surface, update the spec (or add a
backwards-compatible alias) rather than deleting coverage. The Playwright
suites are contract tests: a 404 from a spec means the contract changed.

Quick check that every route referenced by the E2E specs still exists:

```powershell
cd backend
python -m pytest tests/e2e -o addopts="" -q
```

---

## 4. Node-based test runners inside the confined sandbox

Running `npm run test:run` (Vitest) from the agent sandbox can fail with:

```
Error: spawn EPERM
  at ensureServiceIsRunning (.../esbuild/lib/main.js)
```

The confined sandbox denies the piped child-process stdio that esbuild's
service needs. Run frontend tests from a normal terminal, CI, or with the
sandbox's full-access mode — this is an execution-environment limitation,
not a test failure.
