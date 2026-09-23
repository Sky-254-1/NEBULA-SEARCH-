# Nebula Search Engine - Refactoring Plan

**Based on**: REPOSITORY_AUDIT_REPORT.md  
**Date**: 2026-02-07  
**Status**: READY FOR EXECUTION

---

## Executive Summary

This document outlines the complete refactoring plan to transform the Nebula Search Engine repository into an enterprise-grade, production-ready project structure. All changes preserve 100% of existing functionality while improving maintainability, scalability, and developer experience.

---

## Phase 1: Preparation & Safety Measures

### 1.1 Create Safety Tags
```bash
# Create backup tag before any changes
git tag pre-refactor-2026-02-07
git branch backup/pre-refactor

# Create refactoring branch
git checkout -b refactor/structure-cleanup
```

### 1.2 Update .gitignore
Add missing patterns:
```gitignore
# Generated files
full_structure.txt
*.log
*.tmp
*.temp

# Build outputs
dist/
build/
*.pyc
__pycache__/
*.pyo

# OS files
.DS_Store
Thumbs.db
desktop.ini

# IDE files
.vscode/
.idea/
*.swp
*.swo

# AI context files
CLAUDE.md
```

### 1.3 Remove Generated Files
```bash
# Remove files that shouldn't be committed
git rm full_structure.txt
git rm CLAUDE.md
```

---

## Phase 2: Remove Duplicate Repository (CRITICAL)

### 2.1 Analyze Nebula-search-engine--main/

**Action**: Compare with main repository to identify any unique changes.

**Steps**:
1. List all files in duplicate repository
2. Check Git log for recent commits in duplicate
3. Compare file contents with main repository
4. Identify any unique changes or additions

**Decision Point**:
- If no unique changes: DELETE entire folder
- If unique changes exist: MERGE those changes first, then delete

### 2.2 Remove Duplicate Repository

**If no unique changes**:
```bash
# Remove duplicate repository
git rm -rf Nebula-search-engine--main/
git commit -m "refactor: remove duplicate repository Nebula-search-engine--main/"
```

**If unique changes exist**:
```bash
# 1. Apply unique changes to main repository
# 2. Verify all changes are integrated
# 3. Remove duplicate
git rm -rf Nebula-search-engine--main/
git commit -m "refactor: merge and remove duplicate repository"
```

### 2.3 Remove nebula/ Folder

**Action**: Remove duplicate nebula/ folder if not actively used.

```bash
# Check if nebula/ is referenced anywhere
grep -r "nebula/" --include="*.py" --include="*.js" --include="*.ts" --include="*.md" .

# If no references found, remove it
git rm -rf nebula/
git commit -m "refactor: remove duplicate nebula/ folder"
```

---

## Phase 3: Standardize Root Structure

### 3.1 Consolidate Documentation

**Move root-level .md files to docs/**:

| Current Location | New Location | Category |
|------------------|--------------|----------|
| `AUDIO_FEATURES_README.md` | `docs/features/audio.md` | features |
| `AUDIO_IMPLEMENTATION_SUMMARY.md` | `docs/features/audio-implementation.md` | features |
| `AUDIO_INTEGRATION_EXAMPLE.md` | `docs/features/audio-integration.md` | features |
| `AUDIO_QUICK_REFERENCE.md` | `docs/features/audio-quick-reference.md` | features |
| `AUDIO_TESTING_GUIDE.md` | `docs/features/audio-testing.md` | features |
| `ELEVENLABS_QUICKSTART.md` | `docs/features/elevenlabs-setup.md` | features |
| `IOIS_COMPLETE_BUILD.md` | `docs/development/build-complete.md` | development |
| `NEXT_STEPS.md` | `docs/development/next-steps.md` | development |
| `PHASE2_COMPLETE_AUDIT.md` | `docs/archive/phases/phase2-audit.md` | archive |
| `PHASE3_COMPLETE_AUDIT.md` | `docs/archive/phases/phase3-audit.md` | archive |
| `PHASE6_COMPLETE_AUDIT.md` | `docs/archive/phases/phase6-audit.md` | archive |
| `PHASE9_10_COMPLETE.md` | `docs/archive/phases/phase9-10-complete.md` | archive |
| `PRODUCTION_READINESS_FINAL.md` | `docs/archive/production-readiness.md` | archive |
| `UI_UX_COMPLETE_AUDIT.md` | `docs/archive/ui-ux-audit.md` | archive |

**Create docs subdirectories**:
```bash
mkdir -p docs/features
mkdir -p docs/development
mkdir -p docs/archive/phases
```

**Move files**:
```bash
# Use git mv to preserve history
git mv AUDIO_FEATURES_README.md docs/features/audio.md
git mv AUDIO_IMPLEMENTATION_SUMMARY.md docs/features/audio-implementation.md
git mv AUDIO_INTEGRATION_EXAMPLE.md docs/features/audio-integration.md
git mv AUDIO_QUICK_REFERENCE.md docs/features/audio-quick-reference.md
git mv AUDIO_TESTING_GUIDE.md docs/features/audio-testing.md
git mv ELEVENLABS_QUICKSTART.md docs/features/elevenlabs-setup.md
git mv IOIS_COMPLETE_BUILD.md docs/development/build-complete.md
git mv NEXT_STEPS.md docs/development/next-steps.md
git mv PHASE2_COMPLETE_AUDIT.md docs/archive/phases/phase2-audit.md
git mv PHASE3_COMPLETE_AUDIT.md docs/archive/phases/phase3-audit.md
git mv PHASE6_COMPLETE_AUDIT.md docs/archive/phases/phase6-audit.md
git mv PHASE9_10_COMPLETE.md docs/archive/phases/phase9-10-complete.md
git mv PRODUCTION_READINESS_FINAL.md docs/archive/production-readiness.md
git mv UI_UX_COMPLETE_AUDIT.md docs/archive/ui-ux-audit.md

git commit -m "refactor: consolidate documentation into docs/"
```

### 3.2 Consolidate Deployment Folders

**Merge deploy/ and deployments/ into deployment/**:

```bash
# Check contents of both folders
ls -la deploy/
ls -la deployments/

# If they contain different content, merge them
# If they're duplicates, just use one

# Create unified deployment folder
mkdir -p deployment

# Move contents (adjust based on actual content)
git mv deploy/* deployment/ 2>/dev/null || true
git mv deployments/* deployment/ 2>/dev/null || true

# Remove empty folders
git rm -rf deploy deployments

git commit -m "refactor: consolidate deploy/ and deployments/ into deployment/"
```

### 3.3 Standardize Docker Configuration

**Action**: Keep docker/ folder, remove root docker-compose.yml

```bash
# Check if root docker-compose.yml is different from docker/docker-compose.yml
diff docker-compose.yml docker/docker-compose.yml

# If they're the same, remove root version
git rm docker-compose.yml

# If different, merge changes into docker/docker-compose.yml first
# Then remove root version

git commit -m "refactor: standardize docker-compose in docker/ folder"
```

### 3.4 Clean Up Root-Level Files

**Remove or relocate**:
```bash
# Remove nebula-search.html if it's legacy (verify first)
# Move to archive if needed
git rm nebula-search.html

# Remove "update repo structure" file (no extension, unclear purpose)
git rm "update repo structure"

git commit -m "refactor: clean up root-level orphan files"
```

---

## Phase 4: Reorganize Backend Structure

### 4.1 Move Database to Backend

**Current**: `database/` at root level  
**Target**: `backend/database/`

```bash
# Move database folder
git mv database backend/database

# Update any references to database/ in code
# (Will be handled in import cleanup phase)

git commit -m "refactor: move database/ to backend/database/"
```

### 4.2 Reorganize Backend Structure

**Current**:
```
backend/
├── .env.example
├── .gitignore
├── elevenlabs_example.py
├── pytest.ini
├── requirements*.txt
├── app/
│   ├── config.py
│   ├── main.py
│   ├── database/
│   ├── middleware/
│   ├── models/
│   ├── providers/
│   ├── routes/
│   ├── search/
│   └── services/
├── test_helpers/
└── vector/
```

**Target**:
```
backend/
├── .env.example
├── .gitignore
├── pytest.ini
├── requirements.txt
├── requirements-dev.txt
├── requirements.lock
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── search.py
│   │   │   ├── ai.py
│   │   │   ├── audio.py
│   │   │   ├── vector.py
│   │   │   ├── storage.py
│   │   │   └── admin.py
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── rate_limit.py
│   │       └── security.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai.py
│   │   ├── audio.py
│   │   ├── auth.py
│   │   ├── cache.py
│   │   ├── queue.py
│   │   └── search.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── user.py
│   └── workers/
│       ├── __init__.py
│       └── vector_worker.py
├── database/
│   ├── migrations/
│   ├── seeds/
│   └── schema/
├── migrations/ (if using Alembic)
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_*.py
```

**Actions**:
```bash
# 1. Create new structure
cd backend

# 2. Move routes to api/v1/
mkdir -p app/api/v1
git mv app/routes/*.py app/api/v1/
git mv app/routes/__init__.py app/api/v1/ 2>/dev/null || true
git rm -rf app/routes

# 3. Move middleware to api/
git mv app/middleware app/api/middleware

# 4. Create core/ folder and move config
mkdir -p app/core
git mv app/config.py app/core/config.py

# 5. Move vector/ to workers/
git mv vector app/workers/vector_worker
# Update imports in vector files

# 6. Move test_helpers/ to tests/
git mv test_helpers tests/helpers

# 7. Remove elevenlabs_example.py (or move to docs)
git rm elevenlabs_example.py

cd ..

git commit -m "refactor: reorganize backend structure"
```

---

## Phase 5: Reorganize Frontend Structure

### 5.1 Restructure Frontend

**Current**:
```
frontend/src/
├── App.jsx
├── main.jsx
├── api/
├── auth/
├── components/
├── hooks/
├── pages/
├── state/
├── styles/
└── utils/
```

**Target**:
```
frontend/src/
├── app/
│   ├── App.jsx
│   ├── main.jsx
│   └── providers/
│       ├── AuthProvider.jsx
│       └── Router.jsx
├── features/
│   ├── auth/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   └── services/
│   ├── search/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── services/
│   ├── ai/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── services/
│   └── audio/
│       ├── components/
│       ├── hooks/
│       └── services/
├── components/
│   ├── ui/
│   │   ├── Button.jsx
│   │   ├── Modal.jsx
│   │   └── Toast.jsx
│   └── layout/
│       ├── Header.jsx
│       └── Footer.jsx
├── hooks/
│   ├── useAI.js
│   ├── useAudio.js
│   ├── useChat.js
│   ├── useInstallPrompt.js
│   └── useSearch.js
├── services/
│   ├── api/
│   │   ├── ai.js
│   │   ├── audio.js
│   │   ├── auth.js
│   │   ├── search.js
│   │   └── client.js
│   └── storage.js
├── stores/
│   ├── AuthContext.jsx
│   └── SearchContext.jsx
├── utils/
│   └── storage.js
├── styles/
│   └── app.css
└── types/
    └── index.js
```

**Actions**:
```bash
cd frontend/src

# 1. Create new structure
mkdir -p app/providers
mkdir -p features/{auth,search,ai,audio}/{components,hooks,services,pages}
mkdir -p components/{ui,layout}
mkdir -p services/api
mkdir -p stores
mkdir -p types

# 2. Move App.jsx and main.jsx
git mv App.jsx app/
git mv main.jsx app/

# 3. Move auth/ to features/auth/
git mv auth features/auth/
# Move AuthContext to stores/
git mv features/auth/AuthContext.jsx stores/AuthContext.jsx

# 4. Move state/ to stores/
git mv state stores/

# 5. Move api/ to services/api/
git mv api services/api/

# 6. Move utils/
git mv utils/ utils/

# 7. Move styles/
git mv styles/ styles/

# 8. Move hooks/
git mv hooks/ hooks/

# 9. Move components/
git mv components/ components/

# 10. Move pages/
git mv pages/ features/search/pages/

cd ..

git commit -m "refactor: restructure frontend with feature-based organization"
```

---

## Phase 6: Organize Tests

### 6.1 Reorganize Test Structure

**Current**:
```
tests/
├── conftest.py
├── test_*.py (multiple)
└── e2e/
```

**Target**:
```
tests/
├── unit/
│   ├── test_ai.py
│   ├── test_auth.py
│   ├── test_search.py
│   └── ...
├── integration/
│   ├── test_api.py
│   ├── test_database.py
│   └── ...
├── e2e/
│   ├── playwright.config.ts
│   ├── tests/
│   └── ...
├── fixtures/
│   ├── users.py
│   ├── documents.py
│   └── ...
└── conftest.py
```

**Actions**:
```bash
# 1. Create new structure
mkdir -p tests/{unit,integration,fixtures}

# 2. Move unit tests
git mv tests/test_ai.py tests/unit/
git mv tests/test_auth.py tests/unit/
git mv tests/test_search.py tests/unit/
git mv tests/test_vector.py tests/unit/
git mv tests/test_storage.py tests/unit/
git mv tests/test_health.py tests/unit/
git mv tests/test_middleware.py tests/unit/
git mv tests/test_orchestrator.py tests/unit/

# 3. Move integration tests
git mv tests/test_ai_service.py tests/integration/
git mv tests/test_auth_service.py tests/integration/
git mv tests/test_search_service.py tests/integration/
git mv tests/test_cache_service_extended.py tests/integration/
git mv tests/test_search_routes_extended.py tests/integration/
git mv tests/test_vector_routes_extended.py tests/integration/
git mv tests/test_ai_providers_extended.py tests/integration/
git mv tests/test_search_service_extended.py tests/integration/
git mv tests/test_refresh_auth.py tests/integration/

# 4. Move e2e tests (already in place)
# tests/e2e/ already exists

# 5. Move conftest.py to root of tests/
# Already in place

git commit -m "refactor: reorganize tests by type"
```

---

## Phase 7: Organize Scripts

### 7.1 Reorganize Scripts by Purpose

**Current**:
```
scripts/
├── backup.ps1
├── backup.sh
├── build.ps1
├── build.sh
├── logs.ps1
├── logs.sh
├── migrations.ps1
├── migrations.sh
├── reset.ps1
├── reset.sh
├── restore.ps1
├── restore.sh
├── run-dev.ps1
├── run-dev.sh
├── start.ps1
├── start.sh
├── stop.ps1
├── stop.sh
├── test.ps1
└── test.sh
```

**Target**:
```
scripts/
├── build/
│   ├── build.sh
│   └── build.ps1
├── database/
│   ├── migrate.sh
│   ├── migrate.ps1
│   ├── seed.sh
│   ├── seed.ps1
│   ├── backup.sh
│   ├── backup.ps1
│   ├── restore.sh
│   └── restore.ps1
├── development/
│   ├── run-dev.sh
│   └── run-dev.ps1
├── maintenance/
│   ├── reset.sh
│   ├── reset.ps1
│   ├── logs.sh
│   └── logs.ps1
├── testing/
│   ├── test.sh
│   └── test.ps1
└── deploy/
    ├── start.sh
    ├── start.ps1
    ├── stop.sh
    └── stop.ps1
```

**Actions**:
```bash
# 1. Create new structure
mkdir -p scripts/{build,database,development,maintenance,testing,deploy}

# 2. Move build scripts
git mv scripts/build.sh scripts/build/
git mv scripts/build.ps1 scripts/build/

# 3. Move database scripts
git mv scripts/migrations.sh scripts/database/migrate.sh
git mv scripts/migrations.ps1 scripts/database/migrate.ps1
git mv scripts/backup.sh scripts/database/backup.sh
git mv scripts/backup.ps1 scripts/database/backup.ps1
git mv scripts/restore.sh scripts/database/restore.sh
git mv scripts/restore.ps1 scripts/database/restore.ps1

# 4. Move development scripts
git mv scripts/run-dev.sh scripts/development/
git mv scripts/run-dev.ps1 scripts/development/

# 5. Move maintenance scripts
git mv scripts/reset.sh scripts/maintenance/
git mv scripts/reset.ps1 scripts/maintenance/
git mv scripts/logs.sh scripts/maintenance/
git mv scripts/logs.ps1 scripts/maintenance/

# 6. Move testing scripts
git mv scripts/test.sh scripts/testing/
git mv scripts/test.ps1 scripts/testing/

# 7. Move deploy scripts
git mv scripts/start.sh scripts/deploy/
git mv scripts/start.ps1 scripts/deploy/
git mv scripts/stop.sh scripts/deploy/
git mv scripts/stop.ps1 scripts/deploy/

git commit -m "refactor: organize scripts by purpose"
```

---

## Phase 8: Organize Assets

### 8.1 Create Assets Structure

**Current**: No centralized assets folder  
**Target**:
```
assets/
├── images/
│   ├── logos/
│   ├── icons/
│   └── screenshots/
├── fonts/
└── branding/
```

**Actions**:
```bash
# 1. Create assets structure
mkdir -p assets/{images/{logos,icons,screenshots},fonts,branding}

# 2. Move any existing images
# (Check if any exist in public/ or other locations)

# 3. Update references in code

git add assets/
git commit -m "refactor: create centralized assets folder"
```

---

## Phase 9: Centralize Configuration

### 9.1 Create Config Structure

**Current**: Configuration scattered across multiple locations  
**Target**:
```
config/
├── development/
│   └── .env.example
├── staging/
│   └── .env.example
├── production/
│   └── .env.example
└── docker/
    └── nginx/
```

**Actions**:
```bash
# 1. Create config structure
mkdir -p config/{development,staging,production,docker/nginx}

# 2. Move .env.example files
git mv .env.example config/development/
git mv backend/.env.example config/development/backend.env.example

# 3. Move nginx config
git mv nginx/nginx.conf config/docker/nginx/

# 4. Remove empty nginx/ folder
git rm -rf nginx

# 5. Move prometheus.yml
git mv infra/prometheus.yml config/monitoring/
git rm -rf infra

git commit -m "refactor: centralize configuration files"
```

---

## Phase 10: Update Imports and Paths

### 10.1 Backend Import Updates

**Files to update**:
- All Python files in backend/
- All test files
- All configuration files

**Common changes**:
```python
# Before
from database.migrations import ...
from app.routes import ...

# After
from backend.database.migrations import ...
from backend.app.api.v1 import ...
```

**Actions**:
```bash
# Use sed or manual updates to fix imports
# This requires careful review of each file

# Example for database imports
find backend -name "*.py" -exec sed -i 's/from database/from backend.database/g' {} +
find backend -name "*.py" -exec sed -i 's/import database/import backend.database/g' {} +

# Update test imports
find tests -name "*.py" -exec sed -i 's/from app/from backend.app/g' {} +
find tests -name="*.py" -exec sed -i 's/import app/import backend.app/g' {} +

git commit -m "refactor: update imports after restructuring"
```

### 10.2 Frontend Import Updates

**Files to update**:
- All .jsx and .js files in frontend/src/

**Common changes**:
```javascript
// Before
import { AuthContext } from '../auth/AuthContext'
import { searchApi } from '../api/search'

// After
import { AuthContext } from '../stores/AuthContext'
import { searchApi } from '../services/api/search'
```

**Actions**:
```bash
cd frontend/src

# Update imports based on new structure
# This requires manual review of each file

# Example updates
find . -name "*.jsx" -exec sed -i 's|from ../auth/|from ../stores/|g' {} +
find . -name "*.jsx" -exec sed -i 's|from ../api/|from ../services/api/|g' {} +
find . -name "*.jsx" -exec sed -i 's|from ../state/|from ../stores/|g' {} +

cd ../..

git commit -m "refactor: update frontend imports after restructuring"
```

### 10.3 Update Configuration Paths

**Files to update**:
- docker-compose files
- Dockerfiles
- Script files
- Documentation

**Common changes**:
```yaml
# Before
volumes:
  - ./database/migrations:/app/database/migrations

# After
volumes:
  - ./backend/database/migrations:/app/backend/database/migrations
```

**Actions**:
```bash
# Update docker-compose files
sed -i 's|./database/|./backend/database/|g' docker/docker-compose*.yml
sed -i 's|./backend/app|./backend/app|g' docker/docker-compose*.yml

# Update scripts
find scripts -name "*.sh" -exec sed -i 's|cd backend|cd backend|g' {} +
find scripts -name "*.ps1" -exec sed -i 's|cd backend|cd backend|g' {} +

git commit -m "refactor: update configuration paths"
```

---

## Phase 11: Update Documentation

### 11.1 Update README.md

**Update project structure section**:
```markdown
## Project Structure

```
nebula-search-engine/
├── frontend/           # React + Vite application
│   └── src/
│       ├── app/        # App configuration
│       ├── features/   # Feature modules
│       ├── components/ # Shared components
│       ├── hooks/      # Custom hooks
│       ├── services/   # API services
│       └── stores/     # State management
├── backend/            # FastAPI backend
│   └── app/
│       ├── api/        # API endpoints
│       ├── core/       # Core functionality
│       ├── services/   # Business logic
│       └── workers/    # Background workers
├── database/           # Database schemas and migrations
├── docs/               # Documentation
├── tests/              # All tests
├── docker/             # Docker configurations
├── deployment/         # Deployment configs
├── scripts/            # Build and deploy scripts
└── config/             # Environment configurations
```
```

### 11.2 Update docs/FOLDER_STRUCTURE.md

**Update to reflect new structure**

### 11.3 Update All Documentation Links

**Check for broken links**:
```bash
# Find all markdown links
grep -r "\[.*\](.*)" docs/*.md

# Update any links to moved files
# Example: [Setup](SETUP.md) -> [Setup](docs/setup.md)
```

---

## Phase 12: Validation

### 12.1 Run Tests

```bash
# Backend tests
cd backend
pytest --cov=app --cov-report=term-missing

# Frontend tests (if any)
cd frontend
npm test

# E2E tests
npm run e2e:install
npm run e2e
```

### 12.2 Verify Builds

```bash
# Backend build
cd backend
python -m py_compile app/main.py

# Frontend build
cd frontend
npm run build

# Docker build
cd docker
docker compose config
```

### 12.3 Verify Docker

```bash
# Validate docker-compose files
cd docker
docker compose -f docker-compose.dev.yml config
docker compose -f docker-compose.prod.yml config
```

### 12.4 Verify Imports

```bash
# Check for broken imports
cd backend
python -c "import app.main" 2>&1

# Check frontend imports
cd frontend
npm run lint 2>&1 || true
```

### 12.5 Verify API Routes

```bash
# Start backend and check routes
cd backend
uvicorn app.main:app --reload &
curl http://localhost:8000/docs
```

### 12.6 Manual Testing

- [ ] Test authentication flow
- [ ] Test search functionality
- [ ] Test AI features
- [ ] Test audio features
- [ ] Test file uploads
- [ ] Test vector operations

---

## Phase 13: Final Cleanup

### 13.1 Update .gitignore

Ensure all generated files are ignored:
```bash
# Add any missing patterns
echo "*.log" >> .gitignore
echo "*.tmp" >> .gitignore
echo ".DS_Store" >> .gitignore
echo "Thumbs.db" >> .gitignore
```

### 13.2 Remove Empty Folders

```bash
# Remove any empty folders created during migration
find . -type d -empty -delete
```

### 13.3 Final Git Status Check

```bash
# Review all changes
git status

# Review diff
git diff --stat

# Ensure no unintended changes
git diff
```

---

## Phase 14: Create Pull Request

### 14.1 Final Commit

```bash
git add -A
git commit -m "refactor: complete enterprise-grade project restructuring

- Remove duplicate repository (Nebula-search-engine--main/)
- Remove duplicate nebula/ folder
- Consolidate documentation into docs/
- Reorganize backend structure with API versioning
- Restructure frontend with feature-based organization
- Organize tests by type (unit/integration/e2e)
- Reorganize scripts by purpose
- Centralize configuration files
- Update all imports and paths
- Update documentation

Preserves 100% of existing functionality.
All tests passing. All builds successful."
```

### 14.2 Create PR

```bash
# Push to remote
git push origin refactor/structure-cleanup

# Create PR with detailed description
gh pr create --title "refactor: enterprise-grade project restructuring" --body "$(cat REFACTORING_COMPLETE.md)"
```

---

## Rollback Plan

If critical issues are discovered:

```bash
# Rollback to pre-refactor state
git checkout main
git reset --hard pre-refactor-2026-02-07

# Or use backup branch
git checkout backup/pre-refactor
```

---

## Success Metrics

- [x] Audit report completed
- [ ] Duplicate repository removed
- [ ] All documentation consolidated
- [ ] Backend structure reorganized
- [ ] Frontend structure reorganized
- [ ] Tests organized by type
- [ ] Scripts organized by purpose
- [ ] Configuration centralized
- [ ] All imports updated
- [ ] All tests passing
- [ ] All builds successful
- [ ] Docker compose valid
- [ ] Documentation updated
- [ ] No broken links
- [ ] Git history preserved

---

## Timeline

| Phase | Duration | Risk | Status |
|-------|----------|------|--------|
| 1. Preparation | 1 hour | Low | Pending |
| 2. Remove Duplicates | 2 hours | High | Pending |
| 3. Standardize Root | 2 hours | Medium | Pending |
| 4. Reorganize Backend | 3 hours | Medium | Pending |
| 5. Reorganize Frontend | 2 hours | Medium | Pending |
| 6. Organize Tests | 1 hour | Low | Pending |
| 7. Organize Scripts | 1 hour | Low | Pending |
| 8. Organize Assets | 0.5 hours | Low | Pending |
| 9. Centralize Config | 1 hour | Medium | Pending |
| 10. Update Imports | 3 hours | High | Pending |
| 11. Update Docs | 1 hour | Low | Pending |
| 12. Validation | 2 hours | Critical | Pending |
| 13. Final Cleanup | 0.5 hours | Low | Pending |
| 14. Create PR | 0.5 hours | Low | Pending |

**Total Estimated Time**: 20-22 hours

---

## Next Steps

1. ✅ Review this refactoring plan
2. ⚠️ Get approval from team
3. Create backup tag and branch
4. Execute phases sequentially
5. Test after each phase
6. Create PR for review

---

**END OF REFACTORING PLAN**