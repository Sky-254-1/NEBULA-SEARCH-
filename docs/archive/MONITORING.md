# Nebula Search Engine - Monitoring Guide

## Overview

This guide covers monitoring setup, metrics, dashboards, and alerting for Nebula Search Engine production deployments.

## Architecture

### Monitoring Stack

- **Prometheus** - Metrics collection and storage
- **Grafana** - Visualization and dashboards
- **Loki** - Log aggregation
- **Promtail** - Log collection

### Metrics Flow

```
Application → Prometheus Client → Prometheus → Grafana
Logs → Promtail → Loki → Grafana
```

## Quick Start

### Access Dashboards

```bash
# Prometheus
https://your-domain.com:9090

# Grafana
https://grafana.nebula-search.example.com
# Default credentials from .env.production
```

### Verify Metrics Collection

```bash
# Check Prometheus targets
curl https://your-domain.com:9090/metrics

# Verify backend metrics
curl https://your-domain.com/metrics

# Check Prometheus targets page
# Visit: https://your-domain.com:9090/targets
```

## Key Metrics

### Application Metrics

#### HTTP Metrics

```promql
# Request rate (requests per second)
sum(rate(nebula_http_requests_total[5m])) by (method, status)

# Error rate (percentage)
sum(rate(nebula_http_requests_total{status=~"5.."}[5m])) / sum(rate(nebula_http_requests_total[5m])) * 100

# Response time percentiles
histogram_quantile(0.95, sum(rate(nebula_http_request_duration_seconds_bucket[5m])) by (le))
histogram_quantile(0.99, sum(rate(nebula_http_request_duration_seconds_bucket[5m])) by (le))

# Active requests
nebula_http_active_requests
```

#### Search Metrics

```promql
# Search request rate
sum(rate(nebula_http_requests_total{path=~"/api/v1/search.*"}[5m])) by (method)

# Search latency p95
histogram_quantile(0.95, sum(rate(nebula_http_request_duration_seconds_bucket{path=~"/api/v1/search.*"}[5m])) by (le))

# Total search queries
sum(nebula_search_queries_total) by (search_type, backend)
```

#### AI Metrics

```promql
# AI request rate
sum(rate(nebula_http_requests_total{path=~"/api/v1/ai.*"}[5m]))

# AI latency p95
histogram_quantile(0.95, sum(rate(nebula_http_request_duration_seconds_bucket{path=~"/api/v1/ai.*"}[5m])) by (le))
```

#### Cache Metrics

```promql
# Cache hit rate
sum(nebula_cache_hits_total) / (sum(nebula_cache_hits_total) + sum(nebula_cache_misses_total)) * 100

# Cache hits per second
rate(nebula_cache_hits_total[5m])

# Cache misses per second
rate(nebula_cache_misses_total[5m])
```

#### Analytics Metrics

```promql
# Popular queries
topk(10, sum(nebula_popular_queries_total) by (query))

# Zero-result queries
sum(nebula_zero_result_queries_total) by (query)

# Click-through rate
avg(nebula_ctr_percentage) by (period)
```

### Infrastructure Metrics

#### PostgreSQL

```promql
# Database connections
pg_stat_activity_count

# Database size
pg_database_size{datname="nebula"}

# Cache hit ratio
pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read)

# Slow queries
pg_stat_statements_mean_time
```

#### Redis

```promql
# Memory usage
redis_memory_used_bytes

# Connected clients
redis_connected_clients

# Cache hit rate
redis_keyspace_hits / (redis_keyspace_hits + redis_keyspace_misses)

# Commands per second
rate(redis_commands_total[5m])
```

#### System Metrics

```promql
# CPU usage (from node_exporter)
rate(node_cpu_seconds_total{mode!="idle"}[5m])

# Memory usage
node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes

# Disk usage
node_filesystem_avail_bytes / node_filesystem_size_bytes

# Network traffic
rate(node_network_receive_bytes_total[5m])
rate(node_network_transmit_bytes_total[5m])
```

### Business Metrics

#### Search Performance

```promql
# Average search latency
avg(nebula_average_search_latency_seconds)

# Dashboard generation time
histogram_quantile(0.95, sum(rate(nebula_dashboard_generation_time_seconds_bucket[5m])) by (le))
```

#### User Activity

```promql
# Active users (from sessions)
count(redis_connected_clients)

# Document uploads
sum(nebula_click_events_total{event="document_upload"})
```

## Grafana Dashboards

### Pre-configured Dashboards

1. **Nebula Overview** (`nebula-overview.json`)
   - Request rate and response time
   - Error rates
   - Search and AI latency
   - Active connections

### Creating Custom Dashboards

#### Steps

1. Open Grafana: https://grafana.nebula-search.example.com
2. Navigate to **Dashboards** → **New dashboard**
3. Add panel → Select **Prometheus** data source
4. Enter PromQL query
5. Configure visualization settings
6. Save dashboard

#### Example: Search Latency Panel

```yaml
Title: Search Latency (p95)
Query: histogram_quantile(0.95, sum(rate(nebula_http_request_duration_seconds_bucket{path=~"/api/v1/search.*"}[5m])) by (le))
Visualization: Graph
Y-axis: Seconds
Time range: Last 15 minutes
```

## Alerts

### Critical Alerts

#### High Error Rate

```yaml
name: HighErrorRate
expr: sum(rate(nebula_http_requests_total{status=~"5.."}[5m])) / sum(rate(nebula_http_requests_total[5m])) > 0.05
for: 2m
labels:
  severity: critical
annotations:
  summary: "Error rate > 5%"
  description: "Error rate is {{ $value | humanizePercentage }}"
```

#### Service Down

```yaml
name: BackendDown
expr: up{job="nebula-backend"} == 0
for: 1m
labels:
  severity: critical
annotations:
  summary: "Backend service is down"
```

#### Database Connection Issues

```yaml
name: DatabasePoolExhausted
expr: nebula_db_pool_size > 19  #接近上限
for: 5m
labels:
  severity: warning
annotations:
  summary: "Database connection pool nearly full"
```

### Warning Alerts

#### High Response Time

```yaml
name: HighResponseTime
expr: histogram_quantile(0.95, sum(rate(nebula_http_request_duration_seconds_bucket[5m])) by (le)) > 2
for: 5m
labels:
  severity: warning
annotations:
  summary: "Response time p95 > 2s"
```

#### Low Cache Hit Rate

```yaml
name: LowCacheHitRate
expr: sum(nebula_cache_hits_total) / (sum(nebula_cache_hits_total) + sum(nebula_cache_misses_total)) < 0.7
for: 10m
labels:
  severity: warning
annotations:
  summary: "Cache hit rate < 70%"
```

#### Disk Space

```yaml
name: HighMemoryUsage
expr: avg_over_time(node_memory_MemAvailable_bytes[5m]) / node_memory_MemTotal_bytes < 0.2
for: 5m
labels:
  severity: warning
annotations:
  summary: "Memory usage > 80%"
```

### Setup Alerting in Grafana

```yaml
# In Grafana UI:
1. Go to Alerting → Notification channels
2. Add channel (Email, Slack, PagerDuty, etc.)
3. Test notification
4. Go to Alerting → Alert rules
5. Import rules from alerts/
6. Configure contact points
```

## Logs

### Loki Queries

Access via Grafana: **Explore** → **Logs**

#### Common Queries

```logql
# All errors
{job="nebula-backend"} |= "ERROR"

# Warnings
{job="nebula-backend"} |= "WARNING"

# Specific request by ID
{job="nebula-backend"} |= "request_id=abc123"

# Search requests
{job="nebula-backend"} |= "search" |= "POST"

# Slow requests (> 1s)
{job="nebula-backend"} |= "duration" |= "1."

# Database errors
{job="nebula-backend"} |= "database" |= "error"

# Authentication failures
{job="nebula-backend"} |= "authentication" |= "failed"
```

### Log Labels

```
job: nebula-backend
level: info, warning, error, critical
method: GET, POST, PUT, DELETE
path: /api/v1/search, /api/v1/ai, etc.
status: 200, 404, 500, etc.
```

### Structured Logging

Logs are in JSON format (production):

```json
{
  "timestamp": "2024-01-01 12:00:00",
  "level": "INFO",
  "name": "nebula",
  "message": "Request processed",
  "request_id": "abc123"
}
```

## Dashboard Screenshots

### Nebula Overview

Shows:
- Request rate (req/sec)
- Response time p95 and p99
- Error rate percentage
- Active connections
- CPU and memory usage
- Search requests breakdown
- Search latency
- AI request latency

### Recommended Additional Dashboards

1. **Search Performance**
   - Search latency trends
   - Search query volume
   - Zero-result queries
   - Query distribution

2. **Database**
   - Connection pool usage
   - Query performance
   - Cache hit ratio
   - Slow queries

3. **Redis**
   - Memory usage
   - Keyspace hits/misses
   - Command stats
   - Connected clients

4. **Infrastructure**
   - CPU, memory, disk
   - Network I/O
   - Container stats

## Monitoring Best Practices

### Metric Naming

- Use snake_case: `nebula_http_requests_total`
- Include unit in metric name: `_seconds`, `_bytes`, `_total`
- Use `_total` suffix for counters
- Use meaningful labels

### Dashboard Design

1. **Overview first** - Start with high-level health indicators
2. **Drill down** - Links to detailed views
3. **Consistent intervals** - Use same time ranges
4. **Alert thresholds** - Visual indicators
5. **Color coding** - Red/yellow/green

### Alert Design

1. **Actionable** - Only alert when action needed
2. **Appropriate severity** - Critical vs warning
3. **Clear descriptions** - Include context
4. **Routing** - Right team notified
5. **Runbooks** - Link to fix procedures

## Troubleshooting

### Metrics Not Appearing

```bash
# Check Prometheus targets
curl https://your-domain.com:9090/api/v1/targets

# Verify backend exposes /metrics
curl https://your-domain.com/metrics

# Check Prometheus logs
docker compose -f docker-compose.prod.yml logs prometheus

# Verify scrape configuration
docker compose -f docker-compose.prod.yml exec prometheus cat /etc/prometheus/prometheus.yml
```

### High Cardinality Issues

```bash
# Check metric cardinality
curl https://your-domain.com:9090/api/v1/label/__name__/values

# Reduce label values
# Avoid user IDs, session IDs as labels
# Use high cardinality carefully
```

### Logs Not Appearing

```bash
# Check Promtail status
docker compose -f docker-compose.prod.yml logs promtail

# Verify Loki connection
curl https://your-domain.com:3100/ready

# Check Promtail config
docker compose -f docker-compose.prod.yml exec promtail cat /etc/promtail/config.yml
```

### Grafana Dashboard Not Loading

```bash
# Check Grafana logs
docker compose -f docker-compose.prod.yml logs grafana

# Verify data sources
# In Grafana UI: Configuration → Data Sources

# Check provisioning
docker compose -f docker-compose.prod.yml exec grafana ls -la /etc/grafana/provisioning/
```

## Advanced Configuration

### Custom Metrics

Add custom business metrics in `backend/app/main.py`:

```python
from prometheus_client import Counter

# Custom metric
custom_metric = Counter(
    "nebula_custom_operation_total",
    "Description of custom operation",
    ["operation_type"]  # Labels
)

# Increment metric
custom_metric.labels(operation_type="index").inc()
```

### Retention Policies

```yaml
# In infra/prometheus.yml
storage:
  tsdb:
    retention.time: 15d
    retention.size: 10GB

# In infra/loki-config.yml
table_manager:
  retention_period: 168h  # 7 days
```

### External Integrations

#### Datadog

```yaml
# Add to docker-compose.prod.yml
datadog-agent:
  image: datadog/agent:latest
  environment:
    - DD_API_KEY=${DATADOG_API_KEY}
    - DD_PROMETHEUS_METRICS_ENABLED=true
```

#### PagerDuty

```yaml
# In Grafana: Alerting → Contact points
# Add PagerDuty integration key
# Configure alert rules to use PagerDuty
```

## Performance Tuning

### Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 15s  # Adjust based on needs
  evaluation_interval: 15s

# Increase retention for longer history
storage:
  tsdb:
    retention.time: 30d
```

### Grafana

```bash
# Increase resources if needed
# In docker-compose.prod.yml:
deploy:
  resources:
    limits:
      memory: 1G
```

### Loki

```yaml
# For large deployments, use S3 backend
storage:
  s3:
    endpoint: s3.amazonaws.com
    bucketnames: nebula-logs
    region: us-east-1
```

## Security

### Access Control

- Grafana: Enable authentication, use RBAC
- Prometheus: Network restrictions, basic auth
- Loki: Authentik/OAuth proxy

### Data Retention

```yaml
# Configure retention in Prometheus
storage:
  tsdb:
    retention.time: 15d

# Configure retention in Loki
table_manager:
  retention_period: 168h
```

## Support

- Prometheus Docs: https://prometheus.io/docs/
- Grafana Docs: https://grafana.com/docs/
- Loki Docs: https://grafana.com/docs/loki/
- Project Monitoring: https://grafana.nebula-search.example.com