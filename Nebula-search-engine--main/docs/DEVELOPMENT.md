# Development Guide

This guide covers setting up a development environment and understanding the codebase.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Setup](#quick-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Debugging](#debugging)
- [Performance Tuning](#performance-tuning)

## Prerequisites

### Required
- **Python 3.11+** - Backend runtime
- **Node.js 18+** - Frontend runtime
- **PostgreSQL 16+** - Primary database
- **Redis 7+** (optional) - Cache and sessions
- **Git** - Version control

### Optional
- **Docker & Docker Compose** - Containerized development
- **Elasticsearch 8.x** - Vector search capabilities
- **OpenAI API key** - AI features
- **VS Code** - Recommended IDE with extensions:
  - Python (Microsoft)
  - ESLint
  - Prettier
  - GitLens

## Quick Setup

### Option 1: Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/Sky-254-1/Nebula-search-engine-.git
cd Nebula-search-engine--main

# Start development environment
bash scripts/quick-start.sh

# Or using Make
make install
make dev
```

### Option 2: Manual Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp ../.env.example ../.env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm ci

# Start development server
npm run dev
```

## Project Structure

```
Nebula-search-engine--main/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── config.py               # Configuration settings
│   │   ├── database/
│   │   │   ├── engine.py           # Database connection
│   │   │   ├── models/             # SQLAlchemy models
│   │   │   └── migrations/         # Alembic migrations
│   │   ├── middleware/
│   │   │   ├── security.py         # Security middleware
│   │   │   ├── rate_limit.py       # Rate limiting
│   │   │   └── ...
│   │   ├── routes/                 # API endpoints
│   │   │   ├── auth.py
│   │   │   ├── search.py
│   │   │   └── ...
│   │   ├── services/               # Business logic
│   │   │   ├── cache.py
│   │   │   ├── search.py
│   │   │   └── ...
│   │   └── utils/                  # Utility functions
│   ├── tests/
│   │   ├── test_*.py                # Unit tests
│   │   └── e2e/                     # E2E tests
│   ├── requirements.txt
│   ├── pytest.ini
│   └── alembic.ini
│
├── frontend/
│   ├── src/
│   │   ├── components/              # Reusable UI components
│   │   │   ├── common/
│   │   │   ├── layout/
│   │   │   └── ...
│   │   ├── pages/                   # Page components
│   │   ├── context/                 # React contexts
│   │   ├── api/                     # API client
│   │   ├── utils/                   # Utility functions
│   │   ├── hooks/                   # Custom React hooks
│   │   ├── styles/                  # Global styles
│   │   ├── App.tsx                  # Root component
│   │   └── main.tsx                 # Entry point
│   ├── tests/                       # Frontend tests
│   ├── package.json
│   ├── vite.config.ts
│   └── vitest.config.ts
│
├── mobile/                          # React Native mobile app
├── desktop/                         # Electron desktop app
├── docs/                            # Documentation
├── scripts/                         # Utility scripts
├── infra/                           # Infrastructure as code
│   ├── terraform/                   # Terraform configs
│   └── kubernetes/                  # K8s manifests
├── docker-compose.yml               # Production compose
├── docker-compose.dev.yml           # Development compose
├── Makefile                         # Development commands
└── README.md
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow the coding standards in [CONTRIBUTING.md](CONTRIBUTING.md).

### 3. Test Your Changes

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Linting
make lint
```

### 4. Run the Application

```bash
# Start all services
make dev

# Or start individually:
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

## Testing

### Backend Tests

```bash
# Run all tests
cd backend
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_auth.py -v

# Run E2E tests
pytest tests/e2e/ -v
```

### Frontend Tests

```bash
# Run all tests
cd frontend
npm test

# Run with coverage
npm run test:coverage

# Run specific test
npm test -- SearchPage.test.tsx
```

### E2E Tests

```bash
# Install Playwright browsers (first time)
cd frontend
npx playwright install

# Run E2E tests
npm run test:e2e

# Run with UI
npm run test:e2e:ui
```

## Debugging

### Backend Debugging

#### VS Code Launch Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI Debug",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host=0.0.0.0",
        "--port=8000"
      ],
      "jinja": true,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

#### Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Frontend Debugging

#### VS Code Launch Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Vite Debug",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:3000",
      "webRoot": "${workspaceFolder}/frontend/src",
      "sourceMapPathOverrides": {
        "/src/*": "${webRoot}/*"
      }
    }
  ]
}
```

#### React DevTools

Install React DevTools browser extension for component inspection.

## Performance Tuning

### Database Queries

```python
# Use eager loading to avoid N+1 queries
from sqlalchemy.orm import selectinload

result = await db.execute(
    select(User)
    .options(selectinload(User.projects))
    .where(User.id == user_id)
)
```

### Caching

```python
from app.services.cache import cache_service

# Cache expensive operations
@cache_service.cached(ttl=300)  # 5 minutes
async def expensive_operation(param: str):
    # Expensive computation
    return result
```

### API Response Compression

Enable gzip compression in production:

```python
from app.middleware.compression import CompressionMiddleware
app.add_middleware(CompressionMiddleware, minimum_size=1024)
```

### Database Indexes

Add indexes for frequently queried fields:

```python
from sqlalchemy import Index

class User(Base):
    __tablename__ = "users"
    email = Column(String, unique=True, index=True)  # Already indexed
    
    # Add composite index
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
    )
```

## Common Tasks

### Adding a New API Endpoint

1. Create route in `backend/app/routes/your_route.py`
2. Add service logic in `backend/app/services/your_service.py`
3. Register router in `backend/app/main.py`
4. Add frontend API call in `frontend/src/api/client.ts`
5. Create/update frontend page component

### Adding a New Database Model

1. Define model in `backend/app/database/models/`
2. Create migration: `alembic revision --autogenerate -m "description"`
3. Apply migration: `alembic upgrade head`
4. Add service methods to interact with model
5. Create API endpoints

### Adding a New Frontend Page

1. Create page component in `frontend/src/pages/`
2. Add route in `frontend/src/App.tsx` or router config
3. Add CSS styles
4. Export from `frontend/src/pages/index.ts`
5. Add navigation link if needed

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Test connection
psql -U postgres -c "SELECT 1"

# Check connection pool
# Look for pool exhaustion warnings in logs
```

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping

# Test connection
redis-cli ping  # Should return PONG
```

### Port Already in Use

```bash
# Windows: Find process using port
netstat -ano | findstr :8000

# Kill process
taskkill /PID <pid> /F

# Or use different port
uvicorn app.main:app --port 8001
```

### Migration Issues

```bash
# Check current revision
alembic current

# View migration history
alembic history

# Rollback last migration
alembic downgrade -1

# Re-apply migrations
alembic upgrade head
```

## Environment Variables

See `.env.example` for all available options. Key variables:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/nebula

# Security
JWT_SECRET=your-32-char-secret-here
SECRET_KEY=your-32-char-secret-here

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# CORS (comma-separated)
CORS_ORIGINS=http://localhost:3000

# Optional: Redis
REDIS_URL=redis://localhost:6379/0

# Optional: Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# Optional: OpenAI
OPENAI_API_KEY=sk-...
```

## Useful Commands

See `Makefile` for all available commands:

```bash
make help          # Show all commands
make dev           # Start development environment
make test          # Run all tests
make lint          # Run linters
make format        # Format code
make db-migrate    # Run database migrations
make logs          # View logs
make shell         # Open backend shell
make clean         # Clean up
```

## Code Review Guidelines

When reviewing PRs, check:

1. **Functionality**: Does it work as intended?
2. **Tests**: Are there tests for new features?
3. **Security**: Any security vulnerabilities?
4. **Performance**: Any performance issues?
5. **Documentation**: Is it documented?
6. **Style**: Does it follow project conventions?

## Getting Help

- Check existing documentation in `docs/`
- Search GitHub issues
- Ask in GitHub Discussions
- Review similar code in the codebase