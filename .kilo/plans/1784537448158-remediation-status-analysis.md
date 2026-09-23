# Frontend UI/UX Testing — Audit & Plan

**Date:** 2026-07-22  
**Branch:** main  
**HEAD:** `99b886e`  
**Scope:** `frontend/` directory  

---

## 1. Current State

### What exists
- **Test runner:** Vitest (`frontend/package.json`: `test`, `test:ui`, `test:coverage`)
- **Test libs:** `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`
- **E2E:** Playwright referenced in `.github/workflows/ci.yml` (`npm run e2e`)
- **Current unit tests:** 2 files, 9 test cases
  - `frontend/tests/pages.test.tsx` — ForgotPasswordPage, EmailVerificationPage, MFAPage, ResetPasswordPage, BottomNav
  - `frontend/tests/auth.test.tsx` — LoginPage
- **Design docs:** `docs/ux/01-06` covering design system, component library, IA
- **Pages:** 17 route components (Login, Register, Search, AI Chat, Documents, Settings, Dashboard, etc.)
- **Layout:** `Layout.tsx`, `Sidebar.tsx`, `Header.tsx`, `BottomNav.tsx`
- **State:** Zustand stores (`@/state`)

### What is missing or unverified
- No tests for: SearchPage, AIChatPage, DocumentsPage, SettingsPage, DashboardPage, AnalyticsPage, HistoryPage, NotificationsPage, ProfilePage, OfflineLibraryPage, SavedSearchesPage, LandingPage, RegisterPage, DocumentViewerPage
- No tests for layout components: `Layout`, `Sidebar`, `Header`
- No tests for `ProtectedRoute` behavior (redirect, auth state)
- No visual regression / screenshot tests
- No accessibility audits (axe / Lighthouse)
- No responsive breakpoint tests (mobile/tablet/desktop)
- No keyboard-navigation tests for shortcuts documented in `docs/ux/06_Keyboard_Shortcuts_Accessibility.md`
- No tests for error/empty/loading states per `docs/ux/05_Component_Library.md`
- CI e2e step runs `npm run e2e` but there is no local `e2e` script in `package.json`; Playwright config and test directory not confirmed

---

## 2. Assumptions to Validate

| Assumption | Risk if Wrong |
|------------|--------------|
| `npm run test` runs all `frontend/tests/*.test.tsx` via Vitest | Silent test gaps if glob is narrower |
| `npm run e2e` exists and points to Playwright | CI step `npm run e2e` will fail silently or break the workflow |
| Pages import cleanly in test environment (no missing global mocks) | Tests fail at import time, not at assertion time |
| Zustand stores are mockable without page-level fixtures | Auth-dependent pages can’t be unit tested |
| Design tokens / component library are implemented as specified in `docs/ux/04-05` | UI tests will assert against wrong baselines |

---

## 3. Recommended Test Layers

### Layer 1: Unit / Component Tests (Vitest + Testing Library)
Target: every page and layout component listed in `docs/ux/05_Component_Library.md`.

**Priority order:**
1. `ProtectedRoute` — auth gate, redirect behavior
2. `Layout` / `Sidebar` / `Header` — navigation collapse, theme toggle, responsive drawer
3. `SearchPage` — search input, suggestions dropdown, empty state, keyboard shortcut `Ctrl+K`
4. `AIChatPage` — streaming response, citation links, follow-up chips
5. `DocumentsPage` — upload dropzone states (idle, dragover, uploading, success, error)
6. `SettingsPage` — form inputs, save/reset, theme selector
7. `DashboardPage` / `AnalyticsPage` — charts render, date range selector
8. `NotificationsPage` — read/unread states, mark-all-read
9. `HistoryPage` / `SavedSearchesPage` — list rendering, delete action
10. `RegisterPage`, `ForgotPasswordPage`, `ResetPasswordPage`, `EmailVerificationPage`, `MFAPage`, `LoginPage` — partially covered; fill gaps (network failures, validation, accessibility)

**Per-component checklist (from Component Library doc):**
- Responsive layout (mobile, tablet, desktop)
- Keyboard navigation
- Focus indicators (visible)
- ARIA labels/roles
- Color contrast > 4.5:1
- Touch target ≥ 44x44px
- Loading, error, empty, disabled, hover, active states

---

### Layer 2: Integration Tests (Vitest + MSW or fetch mock)
- Auth flow: login → redirect → protected page access
- Search flow: type query → suggestions → execute → results render
- Document upload flow: select file → progress → indexed → appears in list
- Settings persistence: change theme → reload → theme persists
- Offline mode: service worker registration → cached search works

---

### Layer 3: End-to-End Tests (Playwright)
**Critical user journeys:**
1. New user onboarding: Landing → Register → Verify email → Login → Search → Upload doc → Logout
2. Returning user: Login → Search → View history → Re-run search
3. Settings: Login → Settings → Toggle dark mode → Verify across pages
4. AI chat: Search → AI Chat → Ask question → Verify citation rendering
5. Document management: Documents → Upload → Progress → Search within document → Delete
6. Keyboard-first: `Ctrl+K` → Type query → `Enter` → Results → `Esc` to close
7. Mobile responsive: Same flows at 375×812 (iPhone) and 768×1024 (tablet)

---

### Layer 4: UX Quality Audits (non-automated or tool-assisted)
- **Accessibility:** Run `@axe-core/playwright` or Lighthouse on each page
- **Visual regression:** Add Chromatic or Percy if Storybook is introduced; otherwise Playwright screenshot comparison
- **Performance:** Lighthouse CI on key pages (FCP, LCP, CLS)
- **Content/design-system conformance:** Spot-check that components match `docs/ux/04_Design_System.md` tokens and `docs/ux/05_Component_Library.md` specs

---

## 4. Gaps vs Design Docs

| Doc | Claimed / Specified | Evidence in Code | Gap |
|-----|---------------------|------------------|-----|
| `04_Design_System.md` | 8px spacing grid, Inter font, breakpoints, dark mode tokens | Not confirmed — no global CSS/Tailwind config inspection yet | Need to verify Tailwind config matches tokens |
| `05_Component_Library.md` | DropZone, Settings, SearchBar, AI Response Card, Search Result Card components | `SearchPage`, `DocumentsPage`, `AIChatPage` exist; DropZone component not confirmed | Verify component implementations match anatomy/specs |
| `06_Keyboard_Shortcuts_Accessibility.md` | `Ctrl+K`, `Ctrl+,`, `Ctrl+S`, etc. | `pages.test.tsx` has no keyboard tests | Keyboard shortcuts need explicit tests |
| `03_Information_Architecture.md` | Nav structure, page hierarchy | `BottomNav`, `Sidebar` partially tested | IA needs navigation-flow tests |

---

## 5. Recommended Execution Order

1. **Audit package scripts** — confirm `e2e` script exists in `frontend/package.json`; if missing, add it or fix CI
2. **Add `frontend/tests/setup.ts`** — global mocks for `fetch`, `window.matchMedia`, `ResizeObserver`, `IntersectionObserver`
3. **Create component test files for untested pages** — start with Layer 1 priority list above
4. **Add integration tests for 3 critical flows** — auth, search, document upload
5. **Add Playwright e2e config + 3 critical journey tests** — if CI is expected to run them
6. **Add accessibility checks** — axe-core via Playwright or vitest-axe
7. **Run full frontend test suite + coverage** — establish current baseline
8. **Visual regression baseline** — Playwright screenshots or Chromatic Storybook

---

## 6. Open Questions

1. **Should UI/UX testing scope include the uncommitted working-tree changes** in `backend/app/database/repositories/*.py` and `backend/app/routes/admin.py`, or is frontend testing isolated to `frontend/`?
2. **Is Playwright already configured** (`playwright.config.ts`, test directory), or does the CI step `npm run e2e` currently fail because the script is missing?
3. **Should the frontend tests be enforced in CI** with a coverage gate, or is the current “build succeeds” check sufficient?
