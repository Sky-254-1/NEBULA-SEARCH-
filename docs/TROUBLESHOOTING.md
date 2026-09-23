# Nebula Search — Troubleshooting

## Backend won't start

**Symptom:** `ModuleNotFoundError: No module named 'app'`

**Fix:** Run uvicorn from the `backend/` directory:

```bash
cd backend
uvicorn app.main:app --reload
```

## JWT / 401 errors after restart

**Symptom:** Login works once, then tokens fail after server restart.

**Cause:** `JWT_SECRET` was not set; a new random secret is generated each restart.

**Fix:** Set a stable `JWT_SECRET` in `backend/.env`.

## Search returns 502

**Symptom:** `/api/v1/search/web` returns "Search backend error".

**Causes:**
- External API outage (Wikipedia, Brave, SerpAPI)
- Invalid or missing API key for Brave/SerpAPI backends
- Network/firewall blocking outbound HTTPS

**Fix:** Try `backend=wikipedia` first (no key required). Verify API keys in `.env`.

## AI answers return 404

**Symptom:** `/api/v1/ai/ask` returns "No AI answer available".

**Cause:** No `OPENAI_API_KEY` configured and DuckDuckGo has no instant answer for the query.

**Fix:** Set `OPENAI_API_KEY` or rephrase the query.

## CORS errors in browser

**Symptom:** Browser console shows CORS policy blocked.

**Fix:** Add your frontend origin to `CORS_ORIGINS` in `.env`:

```env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:5500
```

## Rate limit 429

**Symptom:** "Rate limit exceeded" after many requests.

**Fix:** Wait 60 seconds or increase `RATE_LIMIT_PER_MINUTE` for development.

## Docker health check fails

**Symptom:** Backend container keeps restarting.

**Fix:** Check logs with `docker compose logs backend`. Ensure port 8000 is not in use.

## Python 3.14 compatibility

If `pip install` fails building `pydantic-core`, use Python 3.11 or 3.12 as specified in the Dockerfile.
