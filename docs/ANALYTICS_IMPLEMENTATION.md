# Search Analytics Dashboard Implementation

## Overview

Production-grade search analytics dashboard for Nebula Search Engine with comprehensive tracking, real-time insights, and background aggregation.

## Architecture

### Database Layer
- **Migration**: `backend/app/database/migrations/010_analytics.sql`
- **Tables**: search_events, click_events, response_time_metrics, analytics_daily, analytics_hourly, query_trends, popular_queries

### Repository Layer
- **File**: `backend/app/database/repositories/analytics_repository.py`
- **Pattern**: Repository pattern with async SQLAlchemy
- **Responsibilities**: Data access, aggregation queries, trend calculations

### Service Layer
- **File**: `backend/app/services/analytics_service.py`
- **Pattern**: Service layer with business logic
- **Features**: Redis caching, cache invalidation, aggregation orchestration

### Background Workers
- **File**: `backend/app/services/analytics_background.py`
- **Scheduler**: Hourly, daily, weekly, monthly aggregation
- **Tasks**: Trending computation, cache refresh, log cleanup

### Metrics & Monitoring
- **File**: `backend/app/services/analytics_metrics.py`
- **Integration**: Prometheus client
- **Metrics**: Search queries, popular queries, zero results, latency, CTR, cache hits

### API Routes
- **File**: `backend/app/routes/analytics_extended.py`
- **Authentication**: JWT + Admin role required
- **Rate Limiting**: 60-120 requests/minute
- **Endpoints**: Dashboard, popular, zero-results, response-times, trends, clicks, users, quality

## API Endpoints

### Public (Authenticated Users)
- `POST /api/v1/analytics/record-search` - Record search event
- `POST /api/v1/analytics/record-click` - Record click event

### Admin Only
- `GET /api/v1/analytics/dashboard?period={24h|7d|30d|90d}` - Dashboard overview
- `GET /api/v1/analytics/popular?limit=10&days=30` - Popular searches
- `GET /api/v1/analytics/zero-results?limit=10&days=30` - Zero-result queries
- `GET /api/v1/analytics/response-times?days=7` - Response time analytics
- `GET /api/v1/analytics/query-trends?period=daily&days=30` - Query trends
- `GET /api/v1/analytics/clicks?days=7` - Click analytics
- `GET /api/v1/analytics/users/{user_id}?days=30` - User analytics
- `GET /api/v1/analytics/quality?days=30` - Search quality metrics

## Redis Caching

### Cache Keys
- `analytics:dashboard:{period}` - 5 minutes TTL
- `analytics:popular:{limit}:{days}` - 5 minutes TTL
- `analytics:response_times:{days}` - 5 minutes TTL
- `analytics:trends:{period}:{days}` - 5 minutes TTL

### Invalidation
- Automatic invalidation on new search/click events
- Background refresh every 5 minutes

## Prometheus Metrics

### Counters
- `nebula_search_queries_total{search_type, backend}` - Total searches
- `nebula_popular_queries_total{query}` - Popular query counts
- `nebula_zero_result_queries_total{query}` - Zero-result queries
- `nebula_analytics_cache_hits_total` - Cache hits
- `nebula_analytics_cache_misses_total` - Cache misses
- `nebula_click_events_total{query}` - Click events

### Gauges
- `nebula_average_search_latency_seconds` - Average latency
- `nebula_ctr_percentage{period}` - Click-through rate

### Histograms
- `nebula_dashboard_generation_time_seconds{period}` - Dashboard generation time

## Performance Targets

- Dashboard generation (cached): <10ms
- Dashboard generation (uncached): <200ms
- Popular searches: <30ms
- Response time report: <30ms
- Trend report: <50ms
- Overall API latency: <100ms

## Security

- JWT authentication required
- Admin role required for analytics endpoints
- Rate limiting enforced
- SQL injection prevention via parameterized queries
- XSS protection via security headers

## Testing

### Test File
- `backend/tests/test_analytics.py`

### Coverage
- Repository layer: CRUD operations
- Service layer: Business logic, caching
- Metrics: Prometheus instrumentation
- API: Endpoint authentication, authorization

## Integration

### Main Application
- Registered in `backend/app/main.py`
- Background worker started in lifespan
- Analytics routes included

### Existing System
- Maintains backward compatibility
- Extends existing search logging
- Integrates with Redis cache service
- Uses existing database connection pool

## Usage Example

```python
# Record a search event
POST /api/v1/analytics/record-search
{
  "query": "fastapi tutorial",
  "search_type": "hybrid",
  "results_count": 10,
  "response_time_ms": 45.5,
  "clicked_result": null,
  "device": "desktop"
}

# Get dashboard
GET /api/v1/analytics/dashboard?period=24h
Authorization: Bearer <admin_token>

Response:
{
  "overview": {
    "total_queries": 285764,
    "unique_users": 1324,
    "average_response_time_ms": 48,
    "zero_result_rate": 2.1,
    "click_through_rate": 81.7
  },
  "popular_searches": [...],
  "response_times": {...},
  "zero_result_queries": [...],
  "query_trends": [...]
}
```

## Maintenance

### Daily
- Aggregate daily statistics
- Clean up expired logs (>90 days)

### Weekly
- Aggregate weekly statistics

### Monthly
- Aggregate monthly statistics
- Archive old analytics data

### Continuous
- Hourly aggregation
- Trending computation (every 6 hours)
- Cache refresh (every 5 minutes)

## Future Enhancements

1. Real-time WebSocket updates for dashboard
2. Advanced ML-based trend detection
3. Anomaly detection for search patterns
4. Custom date range selection
5. Export to CSV/PDF
6. Email reports
7. A/B testing integration
8. User journey tracking