# Nebula Search — Setup Guide

## Prerequisites

- Python 3.11+
- pip
- (Optional) Docker and Docker Compose

## Local Development

### 1. Clone and enter backend

```bash
git clone https://github.com/Sky-254-1/Nebula-search-engine-.git
cd Nebula-search-engine-/backend
```

### 2. Create virtual environment (recommended)

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements-dev.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

- `JWT_SECRET` — random 32+ character string
- `OPENAI_API_KEY` — optional, for AI answers
- `BRAVE_API_KEY` / `SERPAPI_KEY` — optional, for paid search backends

### 5. Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### 6. Serve the frontend

```bash
cd ../frontend
python -m http.server 3000
```

Open http://localhost:3000

## Docker

From the `docker/` directory:

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Running Tests

```bash
cd backend
pytest --cov=app --cov-report=term-missing
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `nebula.db` | SQLite file path |
| `JWT_SECRET` | Yes (prod) | auto-generated | JWT signing key |
| `JWT_EXPIRY_HOURS` | No | `24` | Token lifetime |
| `OPENAI_API_KEY` | No | — | OpenAI-compatible API key |
| `BRAVE_API_KEY` | No | — | Brave Search API key |
| `SERPAPI_KEY` | No | — | SerpAPI key |
| `RATE_LIMIT_PER_MINUTE` | No | `60` | Requests per IP per minute |
| `CORS_ORIGINS` | No | localhost origins | Allowed CORS origins |
| `APP_ENV` | No | `development` | `development`, `production`, `testing` |
