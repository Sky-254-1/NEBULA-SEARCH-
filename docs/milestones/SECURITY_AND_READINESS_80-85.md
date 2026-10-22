# Milestone: Security Hardening & Production Readiness 80-85%

**Created:** 2026-07-29  
**Status:** Complete (local main, pending push to origin/main)  
**Target:** Close 55-60% → 80-85% readiness gap + resolve all open Dependabot/CodeQL alerts

---

## Summary

This milestone covers two major work streams:
1. **Production Readiness 80-85%** — Mount missing routers, harden CORS, add CI gates, add mypy baseline, add 0% coverage tests
2. **Security Alert Remediation** — Fix all 20 open CodeQL alerts (5 issue groups) + 4 Dependabot alert groups

---

## Completed Work

### Production Readiness (Items 1-6)

| # | Item | Branch | Status |
|---|------|--------|--------|
| 1 | Mount mfa.py and oauth.py routers + regression test | `fix/mount-mfa-oauth-routers` | ✅ Merged to main |
| 3 | Harden CORS wildcard footgun | `fix/mount-mfa-oauth-routers` | ✅ Merged to main |
| 4 | 0% coverage tests: entities.py, search_history.py, synonyms.py | `fix/production-readiness-80-85` | ✅ Merged to main |
| 5 | mypy config: 99 noise errors suppressed, baseline 146 | `fix/production-readiness-80-85` | ✅ Merged to main |
| 6 | CI gate: router-mount test + mypy ceiling + coverage floor | `fix/production-readiness-80-85` | ✅ Merged to main |

### Dependabot Alerts (4 groups, 20 vulnerabilities)

| Alert | Package | Scope | Fix | Branch | Status |
|-------|---------|-------|-----|--------|--------|
| react-router GHSA-wrjc-x8rr-h8h6 | react-router-dom 6.x | Direct | Patch bump to 6.30.4 | `fix/dependabot-frontend-alerts` | ✅ Merged to main |
| react-router GHSA-337j-9hxr-rhxg | react-router 6.x | Direct | Patch bump to 6.30.4 | `fix/dependabot-frontend-alerts` | ✅ Merged to main |
| brace-expansion GHSA-mh99-v99m-4gvg | eslint deps | Dev | Requires eslint@10 (breaking) | — | ⚠️ Flagged for human |
| esbuild GHSA-67mh-4wv8-2f99 | vite/vitest deps | Dev | Requires vitest@4 (breaking) | — | ⚠️ Flagged for human |
| prismjs GHSA-x7hr-w5r2-h6wg | react-syntax-highlighter | Direct | Requires v16 (breaking) | — | ⚠️ Flagged for human |

### CodeQL Alerts (5 issue groups, 20 alerts)

| # | Alert IDs | Issue | Branch | Status |
|---|-----------|-------|--------|--------|
| 1 | #39, #28 | Clear-text logging of JWT_SECRET | `fix/codeql-secret-logging` | ✅ Merged to main |
| 2 | #4 | Clear-text storage of API key in legacy HTML | `fix/codeql-apikey-storage` | ✅ Merged to main |
| 3 | #24 | Bad HTML filtering regexp in ingestion.py | `fix/codeql-html-parsing` | ✅ Merged to main |
| 4 | #26, #27 | Information exposure in health_routes.py | `fix/codeql-health-info-exposure` | ✅ Merged to main |
| 5 | #29, #33-43 | Missing permissions in deploy.yml | `fix/codeql-deploy-permissions` | ✅ Merged to main |

---

## Test Results

- **Backend:** 477 passed (up from 473 — 4 new HTML parsing regression tests)
- **Frontend:** 17 passed, 1 pre-existing failure (api.test.tsx navigator.onLine, unrelated)
- **mypy:** 146 errors (down from ~257; 99 optional-dep noise errors suppressed via config)

---

## Pending Human Actions

1. **Push local main to origin/main** — 4 commits ahead of `origin/main` (at `c749c30`)
2. **Enable branch protection** on `main` at https://github.com/Sky-254-1/Nebula-search-engine-/settings/branches
3. **Review 3 remaining Dependabot alerts** requiring breaking major-version bumps:
   - eslint@10 (brace-expansion)
   - vitest@4 (esbuild)
   - react-syntax-highlighter@16 (prismjs)
4. **Create GitHub milestone** in the repo UI to track this work formally
5. **Close resolved CodeQL/Dependabot alerts** in GitHub Security tab after verifying the fixes are on origin/main

---

## Git History (local main)

```
9ecf10d merge: add least-privilege permissions to deploy.yml (CodeQL #29, #33-43)
980f828 fix(security): add least-privilege permissions to deploy.yml (CodeQL #29, #33-43)
337a1d5 merge: fix health endpoint info exposure (CodeQL #26, #27)
f7d73bf fix(security): log exceptions server-side, return generic errors in health API (CodeQL #26, #27)
c749c30 merge: replace regex HTML stripping with BeautifulSoup (CodeQL #24)
c1a70c4 fix(security): replace regex HTML stripping with BeautifulSoup parser (CodeQL #24)
1697a63 merge: fix API key storage in legacy HTML (CodeQL #4)
2ed443e fix(security): use sessionStorage for config, strip apiKey from persistence (CodeQL #4)
83b8e89 merge: fix clear-text secret logging (CodeQL #39, #28)
84e66e2 fix(security): redact secrets in stdout/logs (CodeQL #39, #28)
da99edf merge: fix react-router-dom Dependabot alerts (GHSA-wrjc-x8rr-h8h6, GHSA-337j-9hxr-rhxg)
d03c0a8 fix(deps): bump react-router-dom to 6.30.4
5411de8 merge: CI gates, mypy baseline, 0% coverage tests
0dae3b8 ci+types+tests: router-mount regression, mypy baseline ceiling, 0% coverage tests
721f3f8 merge: mount mfa/oauth routers, CORS wildcard hardening, router-mount regression test