# Nebula Search - Makefile
# Common development and deployment commands

.PHONY: help
help: ## Show this help message
	@echo "Nebula Search - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

# Development
.PHONY: install
install: ## Install all dependencies (backend + frontend)
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm ci

.PHONY: dev
dev: ## Start development environment
	@echo "Starting development environment..."
	docker compose -f docker-compose.dev.yml up --build

.PHONY: dev-down
dev-down: ## Stop development environment
	@echo "Stopping development environment..."
	docker compose -f docker-compose.dev.yml down

.PHONY: logs
logs: ## Show logs from all services
	docker compose -f docker-compose.dev.yml logs -f

# Testing
.PHONY: test
test: ## Run all tests (backend + frontend)
	@echo "Running backend tests..."
	cd backend && pytest tests/ -v --tb=short
	@echo "Running frontend tests..."
	cd frontend && npm test -- --run

.PHONY: test-backend
test-backend: ## Run backend tests only
	cd backend && pytest tests/ -v --tb=short

.PHONY: test-frontend
test-frontend: ## Run frontend tests only
	cd frontend && npm test -- --run

.PHONY: test-e2e
test-e2e: ## Run E2E tests
	@echo "Starting services for E2E tests..."
	docker compose -f docker-compose.prod.yml up -d postgres redis elasticsearch
	sleep 10
	@echo "Running backend E2E tests..."
	cd backend && pytest tests/e2e/ -v --tb=short
	@echo "Running Playwright E2E tests..."
	cd frontend && npm run test:e2e

.PHONY: lint
lint: ## Run linting on frontend and backend
	cd frontend && npm run lint
	@echo "Running mypy on backend..."
	cd backend && mypy app/ || true

.PHONY: typecheck
typecheck: ## Run type checking
	cd frontend && npm run typecheck
	cd backend && mypy app/

# Database
.PHONY: db-migrate
db-migrate: ## Run database migrations
	@echo "Running migrations..."
	docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head

.PHONY: db-rollback
db-rollback: ## Rollback last migration
	docker compose -f docker-compose.prod.yml exec -T backend alembic downgrade -1

.PHONY: db-shell
db-shell: ## Open PostgreSQL shell
	docker compose -f docker-compose.prod.yml exec postgres psql -U nebula -d nebula

.PHONY: db-seed
db-seed: ## Seed database with initial data
	@echo "Seeding database..."
	cd backend && python -m app.database.seed

# Build
.PHONY: build
build: ## Build all Docker images
	@echo "Building production images..."
	docker compose -f docker-compose.prod.yml build

.PHONY: build-backend
build-backend: ## Build backend Docker image
	docker build -t nebula-backend:latest -f docker/Dockerfile.prod .

.PHONY: build-frontend
build-frontend: ## Build frontend
	cd frontend && npm run build

# Deploy
.PHONY: deploy
deploy: ## Deploy to production
	@echo "Deploying to production..."
	./scripts/deploy.ps1

.PHONY: deploy-staging
deploy-staging: ## Deploy to staging
	@echo "Deploying to staging..."
	git push origin develop

.PHONY: verify
verify: ## Verify deployment
	@echo "Verifying deployment..."
	./scripts/verify-deployment.ps1

# Cleanup
.PHONY: clean
clean: ## Clean build artifacts and temporary files
	@echo "Cleaning up..."
	cd backend && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd frontend && rm -rf dist node_modules/.vite 2>/dev/null || true
	docker system prune -f

.PHONY: reset
reset: ## Reset everything (WARNING: deletes all data)
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose -f docker-compose.prod.yml down -v; \
		rm -rf backend/storage frontend/dist; \
	fi

# Monitoring
.PHONY: logs-backend
logs-backend: ## Show backend logs
	docker compose -f docker-compose.prod.yml logs -f backend

.PHONY: logs-worker
logs-worker: ## Show worker logs
	docker compose -f docker-compose.prod.yml logs -f worker

.PHONY: ps
ps: ## Show running services
	docker compose -f docker-compose.prod.yml ps

# Utilities
.PHONY: shell
shell: ## Open shell in backend container
	docker compose -f docker-compose.prod.yml exec backend bash

.PHONY: generate-secrets
generate-secrets: ## Generate secure secrets for production
	@echo "Generating secrets..."
	pwsh scripts/generate-secrets.ps1

.PHONY: backup-db
backup-db: ## Backup PostgreSQL database
	@echo "Backing up database..."
	mkdir -p database/backups
	docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U nebula nebula > database/backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup saved to database/backups/"

.PHONY: restore-db
restore-db: ## Restore PostgreSQL database from backup
	@echo "Restoring database..."
	@if [ -z "$(FILE)" ]; then echo "Usage: make restore-db FILE=backup.sql"; exit 1; fi
	docker compose -f docker-compose.prod.yml exec -T postgres psql -U nebula -d nebula < $(FILE)

# Health checks
.PHONY: health
health: ## Check health of all services
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | jq . || echo "Backend: ❌"
	@curl -s http://localhost:9000/minio/health/live | grep OK && echo "MinIO: ✅" || echo "MinIO: ❌"
	@docker compose -f docker-compose.prod.yml exec -T redis redis-cli ping | grep PONG && echo "Redis: ✅" || echo "Redis: ❌"