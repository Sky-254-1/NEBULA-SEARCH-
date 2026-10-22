# Performance Tuning Guide

This guide covers optimizing Nebula Search for production workloads.

---

## Architecture Overview

### Bottleneck Analysis

```
User Request → API → Database → External APIs → Response
                 │        │          │
                 │        │          └─→ External Latency (50-500ms)
                 │        └─→ Database Query (5-50ms)
                 └─→ Application Logic (1-10ms)
```

### Target Latencies

| Endpoint Type | P50 Target | P95 Target | P99 Target |
|---------------|-----------|-----------|-----------|
| Health Check | < 10ms | < 50ms | < 100ms |
| Auth Login | < 100ms | < 200ms | < 500ms |
| Search Web | < 500ms | < 2s | < 5s |
| AI Answer | < 2s | < 5s | < 10s |
| Document Upload | < 1s | < 3s | < 10s |

---

## Database Optimization

### Indexes

```sql
-- Users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Sessions table
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_session_id ON sessions(session_id);
CREATE INDEX idx_sessions_refresh_token_hash ON sessions(refresh_token_hash);

-- Search logs
CREATE INDEX idx_search_logs_user_id ON search_logs(user_id);
CREATE INDEX idx_search_logs_searched_at ON search_logs(searched_at DESC);

-- Documents
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_content_hash ON documents(content_hash);

-- Chunks
CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_chunks_chunk_index ON document_chunks(chunk_index);

-- Citations
CREATE INDEX idx_citations_user_id ON citations(user_id);
CREATE INDEX idx_citations_query ON citations(query);
```

### Connection Pooling

```python
# Backend: app/database/engine.py
async def connect() -> DatabaseConnection:
    if settings.uses_postgres:
        import asyncpg
        
        # Pool configuration
        pool = await asyncpg.create_pool(
            dsn=settings.database_url.replace("postgresql+asyncpg://", "postgresql://"),
            min_size=5,
            max_size=20,
            max_queries=50000,
            max_inactive_connection_lifetime=300,
            timeout=30,
        )
        
        class PostgresConnection(DatabaseConnection):
            async def execute(self, sql: str, params: tuple = ()) -> Any:
                return await pool.execute(_adapt_sql(sql), *params)
            # ... rest of implementation
```

### Query Optimization

```python
# ❌ Bad: N+1 queries
for doc_id in doc_ids:
    doc = await db.fetchone("SELECT * FROM documents WHERE id = ?", (doc_id,))

# ✅ Good: Single query
placeholders = ",".join("?" * len(doc_ids))
docs = await db.fetchall(
    f"SELECT * FROM documents WHERE id IN ({placeholders})", 
    doc_ids
)
```

### Slow Query Detection

```sql
-- Enable slow query logging (PostgreSQL)
SET slow_query_log = on;
SET long_query_time = 1.0;

-- Find slow queries
SELECT query, calls, mean_time, total_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

---

## Caching Strategy

### Cache Hierarchy

```
Browser Cache (localStorage)
    ↓
Redis Cache (distributed)
    ↓
In-Memory Cache (fallback)
    ↓
Database
    ↓
External APIs
```

### Cache Keys

```python
# Search caching
cache_key = f"search:{query}:{backends}:{page}:{page_size}"

# AI answer caching
cache_key = f"ai:{hashlib.sha256(prompt.encode()).hexdigest()}"

# User settings
cache_key = f"settings:{user_id}"

# Search history (short TTL)
cache_key = f"history:{user_id}"
```

### Cache Invalidation

```python
async def invalidate_prefix(prefix: str) -> None:
    """Invalidate all cache entries matching prefix."""
    if self._redis:
        keys = [key async for key in self._redis.scan_iter(match=f"{prefix}*")]
        if keys:
            await self._redis.delete(*keys)
        return
    for key in list(self._memory):
        if key.startswith(prefix):
            del self._memory[key]
```

---

## Redis Configuration

### Production Settings

```yaml
# docker/docker-compose.yml
redis:
  image: redis:7-alpine
  command: redis-server --maxmemory-policy allkeys-lru --maxmemory 256mb
  volumes:
    - redis-data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
```

### Cache Warm-up

```python
# scripts/cache_warmup.py
async def warmup_cache():
    """Pre-populate hot search queries and AI prompts."""
    hot_queries = await db.fetchall(
        "SELECT query FROM search_logs GROUP BY query ORDER BY COUNT(*) DESC LIMIT 100"
    )
    
    for query in hot_queries:
        # Warm search cache
        await run_web_search(query["query"], "wikipedia", 1, 10)
```

---

## Load Testing

### k6 Script

```javascript
// load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '1m', target: 100 },
    { duration: '3m', target: 100 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const res = http.get('http://localhost:8000/api/v1/health');
  check(res, {
    'is status 200': (r) => r.status === 200,
    'response time < 100ms': (r) => r.timings.duration < 100,
  });
  sleep(1);
}
```

### Run Tests

```bash
# Install k6
wget https://github.com/grafana/k6/releases/download/v0.48.0/k6-v0.48.0-linux-amd64.tar.gz
tar -xzf k6-v0.48.0-linux-amd64.tar.gz

# Run load test
./k6 run load-test.js
```

### Results Checklist

- ✅ P50 response time < target
- ✅ P95 response time < target
- ✅ Error rate < 1%
- ✅ CPU utilization < 80%
- ✅ Memory utilization < 80%
- ✅ No connection pool exhaustion

---

## Frontend Optimization

### Code Splitting

```javascript
// React lazy loading
const HistoryPage = lazy(() => 
  import('./pages/HistoryPage').then((m) => ({ default: m.HistoryPage }))
);
```

### Image Optimization

```html
<!-- Preload critical resources -->
<link rel="preload" href="/manifest.json" as="manifest">
<link rel="preload" href="/src/styles/app.css" as="style">
```

### Bundle Analysis

```bash
cd frontend
npm run build -- --report

# Or use webpack-bundle-analyzer
npx webpack-bundle-analyzer dist/report.html
```

### Service Worker

```javascript
// frontend/public/sw.js
const CACHE_NAME = 'nebula-v1';
const ASSETS = [
  '/',
  '/index.html',
  '/src/styles/app.css',
  '/manifest.json',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)));
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((response) => 
      response || fetch(e.request)
    )
  );
});
```

---

## Profiling

### Python Profiling

```bash
# Profile a specific endpoint
python -m cProfile -o profile.out -m uvicorn app.main:app --reload

# Analyze results
snakeviz profile.out
```

### JavaScript Profiling

```javascript
// In browser DevTools
performance.mark('start-search');
await search(query);
performance.mark('end-search');
performance.measure('search', 'start-search', 'end-search');

const measures = performance.getEntriesByType('measure');
console.log(measures[0].duration); // ms
```

### Database Profiling

```sql
-- Enable query profiling
SET profiling = 1;

-- Run queries
SELECT * FROM documents WHERE user_id = 1;
SELECT * FROM search_logs WHERE user_id = 1;

-- View profile
SHOW PROFILES;
SHOW PROFILE FOR QUERY 1;
```

---

## Monitoring Checklist

### Metrics to Track

| Metric | Alert Threshold |
|--------|----------------|
| Response time P95 | > 2s |
| Error rate | > 1% |
| Cache hit rate | < 70% |
| Database connections | > 80% pool |
| CPU utilization | > 80% |
| Memory utilization | > 85% |
| Queue depth | > 1000 jobs |

### Health Check Endpoints

```python
# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

---

## Optimization Priority

1. **High Priority** (Impact > 50%)
   - Database indexes
   - Redis caching
   - Query optimization

2. **Medium Priority** (Impact 10-50%)
   - Frontend code splitting
   - CDN for static assets
   - Connection pooling

3. **Low Priority** (Impact < 10%)
   - Micro-optimizations
   - Language-level tweaks

---

*For support, see [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)*
