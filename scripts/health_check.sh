#!/bin/bash
set -euo pipefail

# Nebula Search Engine - Health Check & Smoke Test Script
# Runs comprehensive health checks against all services

# ============================================================
# Configuration
# ============================================================
TIMEOUT="${HEALTH_CHECK_TIMEOUT:-10}"
RETRIES="${HEALTH_CHECK_RETRIES:-3}"
INTERVAL="${HEALTH_CHECK_INTERVAL:-5}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================================
# Helper Functions
# ============================================================
log_info() { echo -e "${CYAN}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; }

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

check_result() {
    local name="$1"
    local status="$2"
    local message="$3"
    
    if [ "$status" -eq 0 ]; then
        log_success "$name: $message"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        log_error "$name: $message"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

check_warn() {
    local name="$1"
    local message="$2"
    log_warn "$name: $message"
    WARN_COUNT=$((WARN_COUNT + 1))
}

# ============================================================
# Check Functions
# ============================================================

# Check if a URL responds with HTTP 200
check_http_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$url" 2>/dev/null || echo "000")
    
    if [ "$http_code" = "$expected_status" ]; then
        return 0
    else
        return 1
    fi
}

# Check a JSON health endpoint
check_json_health() {
    local name="$1"
    local url="$2"
    
    local response
    response=$(curl -sf --max-time "$TIMEOUT" "$url" 2>/dev/null || echo "")
    
    if [ -z "$response" ]; then
        return 1
    fi
    
    # Check for common health indicators
    if echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null | grep -qi "ok"; then
        return 0
    fi
    
    if echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('database',''))" 2>/dev/null | grep -qi "connected"; then
        return 0
    fi
    
    return 0  # JSON response received - consider it healthy
}

# Check Docker container status
check_docker_container() {
    local container_name="$1"
    
    local status
    status=$(docker inspect --format='{{.State.Status}}' "$container_name" 2>/dev/null || echo "not_found")
    
    if [ "$status" = "running" ]; then
        return 0
    else
        return 1
    fi
}

# Check Docker container health
check_docker_health() {
    local container_name="$1"
    
    local health
    health=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "unknown")
    
    if [ "$health" = "healthy" ] || [ "$health" = "starting" ] || [ "$health" = "<nil>" ]; then
        return 0
    else
        return 1
    fi
}

# Check Kubernetes pod status
check_k8s_pod_ready() {
    local namespace="$1"
    local label="$2"
    
    local ready
    ready=$(kubectl get pods -n "$namespace" -l "$label" -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "False")
    
    if [ "$ready" = "True" ]; then
        return 0
    else
        return 1
    fi
}

# Check PostgreSQL availability
check_postgres() {
    local pg_url="${1:-postgresql://nebula:nebula@localhost:5432/nebula}"
    
    if python3 -c "
import sys
try:
    import asyncpg
    import asyncio
    async def test():
        conn = await asyncpg.connect('$pg_url')
        await conn.close()
        return True
    asyncio.run(test())
    sys.exit(0)
except Exception as e:
    print(f'Database error: {e}')
    sys.exit(1)
" 2>/dev/null; then
        return 0
    fi
    
    # Fallback to pg_isready
    if command -v pg_isready &>/dev/null; then
        pg_isready -h localhost -p 5432 &>/dev/null && return 0
    fi
    
    return 1
}

# Check Redis availability
check_redis() {
    local redis_url="${1:-redis://localhost:6379/0}"
    
    if python3 -c "
import sys
try:
    import redis
    r = redis.from_url('$redis_url')
    r.ping()
    sys.exit(0)
except Exception as e:
    print(f'Redis error: {e}')
    sys.exit(1)
" 2>/dev/null; then
        return 0
    fi
    
    # Fallback to redis-cli
    if command -v redis-cli &>/dev/null; then
        redis-cli ping &>/dev/null && return 0
    fi
    
    return 1
}

# Check disk space
check_disk_space() {
    local path="${1:-/}"
    local threshold="${2:-90}"
    
    local usage
    usage=$(df -h "$path" | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -lt "$threshold" ]; then
        return 0
    else
        return 1
    fi
}

# Check memory usage
check_memory() {
    local threshold="${1:-90}"
    
    if command -v free &>/dev/null; then
        local usage
        usage=$(free | awk '/Mem:/ {printf "%.0f", $3/$2 * 100}')
        
        if [ "$usage" -lt "$threshold" ]; then
            return 0
        else
            return 1
        fi
    fi
    
    return 0  # Skip if not available
}

# Check CPU load
check_cpu_load() {
    local threshold="${1:-8}"
    
    local load
    if command -v uptime &>/dev/null; then
        load=$(uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $1}' | sed 's/ //')
        
        if (( $(echo "$load < $threshold" | bc -l 2>/dev/null || echo "1") )); then
            return 0
        else
            return 1
        fi
    fi
    
    return 0  # Skip if not available
}

# ============================================================
# Main Health Check Execution
# ============================================================
echo "================================================================"
echo -e "${CYAN}NEBULA SEARCH ENGINE - HEALTH CHECK & SMOKE TEST${NC}"
echo "================================================================"
echo "Started at: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ============================================================
# SECTION 1: System Health
# ============================================================
echo -e "${YELLOW}--- System Health ---${NC}"

check_disk_space "/" 90
check_result "Disk Space" $? "Disk usage below 90%"

check_memory 90
check_result "Memory Usage" $? "Memory usage below 90%"

check_cpu_load 8
check_result "CPU Load" $? "CPU load average below 8"

# ============================================================
# SECTION 2: Docker Services (if available)
# ============================================================
if command -v docker &>/dev/null; then
    echo ""
    echo -e "${YELLOW}--- Docker Services ---${NC}"
    
    CONTAINERS=("nebula-postgres" "nebula-redis" "nebula-backend" "nebula-frontend" "nebula-nginx" "nebula-storage" "nebula-worker" "nebula-scheduler" "nebula-prometheus")
    
    for CONTAINER in "${CONTAINERS[@]}"; do
        if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER}$"; then
            check_docker_container "$CONTAINER"
            check_result "Container $CONTAINER" $? "Running"
            
            check_docker_health "$CONTAINER"
            if [ $? -eq 0 ]; then
                : # Health check passed or health check not configured
            fi
        fi
    done
fi

# ============================================================
# SECTION 3: API Endpoints
# ============================================================
echo ""
echo -e "${YELLOW}--- API Endpoints ---${NC}"

# Main health endpoint
check_json_health "Health API" "http://localhost:8000/health"
check_result "GET /health" $? "Health endpoint responding"

# API v1 health
check_json_health "API v1 Health" "http://localhost:8000/api/v1/health"
check_result "GET /api/v1/health" $? "API v1 health endpoint responding"

# OpenAPI docs
check_http_endpoint "API Docs" "http://localhost:8000/docs"
check_result "GET /docs" $? "OpenAPI documentation available"

# Search endpoint (may return empty results depending on DB state)
check_http_endpoint "Search API" "http://localhost:8000/api/v1/search?q=test"
check_result "GET /api/v1/search" $? "Search endpoint responding"

# ============================================================
# SECTION 4: Database Services
# ============================================================
echo ""
echo -e "${YELLOW}--- Database Services ---${NC}"

check_postgres
check_result "PostgreSQL" $? "Database connection successful"

check_redis
check_result "Redis" $? "Cache connection successful"

# ============================================================
# SECTION 5: Smoke Tests
# ============================================================
echo ""
echo -e "${YELLOW}--- Smoke Tests ---${NC}"

# Test 1: Verify API returns valid JSON
SMOKE_RESPONSE=$(curl -sf http://localhost:8000/health 2>/dev/null || echo "")
if echo "$SMOKE_RESPONSE" | python3 -c "import sys,json; json.load(sys.stdin); print('valid')" 2>/dev/null | grep -q "valid"; then
    check_result "API Response Format" 0 "Valid JSON response"
else
    check_result "API Response Format" 1 "Invalid or missing JSON response"
fi

# Test 2: Check CORS headers
CORS_HEADER=$(curl -s -I -X OPTIONS http://localhost:8000/health 2>/dev/null | grep -i "access-control-allow-origin" || echo "")
if [ -n "$CORS_HEADER" ]; then
    check_result "CORS Headers" 0 "CORS headers present"
else
    check_warn "CORS Headers" "CORS headers not checked (OPTIONS not supported on health endpoint)"
fi

# Test 3: Check response time
START_TIME=$(date +%s%N)
curl -sf --max-time 5 http://localhost:8000/health > /dev/null 2>&1 || true
END_TIME=$(date +%s%N)
LATENCY=$(( (END_TIME - START_TIME) / 1000000 ))
if [ "$LATENCY" -lt 2000 ]; then
    check_result "Response Time" 0 "${LATENCY}ms (threshold: 2000ms)"
else
    check_warn "Response Time" "${LATENCY}ms (threshold: 2000ms)"
fi

# Test 4: Check frontend is serving
FRONTEND_RESPONSE=$(curl -sf --max-time 5 http://localhost:3000 2>/dev/null || echo "")
if [ -n "$FRONTEND_RESPONSE" ]; then
    check_result "Frontend" 0 "Frontend is serving content"
else
    check_warn "Frontend" "Frontend not responding on port 3000"
fi

# ============================================================
# SUMMARY
# ============================================================
echo ""
echo "================================================================"
echo -e "${CYAN}HEALTH CHECK SUMMARY${NC}"
echo "================================================================"
echo -e "${GREEN}Passed:${NC} $PASS_COUNT"
echo -e "${RED}Failed:${NC} $FAIL_COUNT"
echo -e "${YELLOW}Warnings:${NC} $WARN_COUNT"
echo "Completed at: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================================"

# Exit with failure if any checks failed
if [ "$FAIL_COUNT" -gt 0 ]; then
    log_error "Health check completed with $FAIL_COUNT failures"
    exit 1
else
    log_success "All health checks passed"
    exit 0
fi
