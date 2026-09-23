# Integration Guide — v1.1

## 1. Backend + Vector indexing

```bash
cd backend
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Optional dedicated worker (when using Redis queue):

```bash
npm run vector:worker
```

Upload flow: `POST /api/v1/storage/documents` → auto-queued index → `GET /api/v1/vector/documents/{id}/status`

Search indexed content: `POST /api/v1/vector/search`

## 2. Frontend (unchanged)

```bash
cd frontend && npm install && npm run dev
```

## 3. E2E tests

```bash
npm install
npm run e2e:install
# Start backend + frontend, then:
npm run e2e
```

CI starts both servers automatically when `CI=true`.

## 4. Mobile (Capacitor)

```bash
cd mobile
npm install
npm run build          # builds frontend + cap sync
npx cap add android    # first time
npx cap open android
```

Set API URL in frontend `.env`:

```
VITE_API_URL=https://your-api.example.com
```

## 5. Docker full stack

```bash
cd docker && docker compose up --build
```

Docker image includes `backend/vector` module.

## Environment variables (new / relevant)

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Optional OpenAI embeddings |
| `STORAGE_ROOT` | Root for uploads, vectors, indexes |
| `REDIS_URL` | Background job queue (optional) |
