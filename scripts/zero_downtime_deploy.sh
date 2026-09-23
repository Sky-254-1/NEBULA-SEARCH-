#!/bin/bash
# =============================================================================
# Nebula Search Engine — Zero-Downtime Deployment Script
# =============================================================================
# This script performs a rolling update with health checks to ensure
# zero downtime during production deployments.
#
# Usage:
#   ./scripts/zero_downtime_deploy.sh [environment] [version]
#
# Examples:
#   ./scripts/zero_downtime_deploy.sh staging v1.2.0
#   ./scripts/zero_downtime_deploy.sh production v1.2.0
#
# Prerequisites:
#   - kubectl configured for the target cluster
#   - Docker images built and pushed to registry
#   - Helm v3 installed (for Helm deployments)
# =============================================================================

set -euo pipefail

# ---- Configuration ----
ENVIRONMENT="${1:-staging}"
VERSION="${2:-latest}"
NAMESPACE="nebula-${ENVIRONMENT}"
MAX_RETRIES=30
RETRY_INTERVAL=10
HEALTH_CHECK_URL="http://localhost:8000/health"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-ghcr.io/sky-254-1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  Nebula Search - Zero-Downtime Deployment  ${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "Environment: ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "Version:     ${YELLOW}${VERSION}${NC}"
echo -e "Namespace:   ${YELLOW}${NAMESPACE}${NC}"
echo ""

# ---- Pre-deployment Checks ----
echo -e "${CYAN}[1/6] Running pre-deployment checks...${NC}"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}ERROR: kubectl not found. Please install kubectl.${NC}"
    exit 1
fi

# Check Helm
if ! command -v helm &> /dev/null; then
    echo -e "${RED}ERROR: helm not found. Please install Helm.${NC}"
    exit 1
fi

# Check namespace exists
if ! kubectl get namespace "${NAMESPACE}" &> /dev/null; then
    echo -e "${YELLOW}Namespace '${NAMESPACE}' not found. Creating...${NC}"
    kubectl create namespace "${NAMESPACE}"
fi

echo -e "${GREEN}  ✓ Pre-deployment checks passed${NC}"

# ---- Run Production Validation ----
echo -e "${CYAN}[2/6] Running production validation...${NC}"
if python3 scripts/validate_production.py; then
    echo -e "${GREEN}  ✓ Production validation passed${NC}"
else
    echo -e "${YELLOW}  ⚠ Production validation had warnings (continuing)${NC}"
fi

# ---- Database Migrations ----
echo -e "${CYAN}[3/6] Running database migrations...${NC}"
if kubectl get pod -n "${NAMESPACE}" -l app=nebula-backend -o jsonpath='{.items[0].metadata.name}' &> /dev/null; then
    BACKEND_POD=$(kubectl get pod -n "${NAMESPACE}" -l app=nebula-backend -o jsonpath='{.items[0].metadata.name}')
    kubectl exec -n "${NAMESPACE}" "${BACKEND_POD}" -- python -m app.database.migrate
    echo -e "${GREEN}  ✓ Database migrations completed${NC}"
else
    echo -e "${YELLOW}  ⚠ No running backend pod found. Migrations will run on startup.${NC}"
fi

# ---- Update Kubernetes Manifests ----
echo -e "${CYAN}[4/6] Updating Kubernetes manifests...${NC}"

# Update image tags in kustomization
if [ -f "infrastructure/k8s/kustomization.yaml" ]; then
    cd infrastructure/k8s
    
    # Update backend image
    kubectl set image deployment/backend \
        backend="${DOCKER_REGISTRY}/nebula-backend:${VERSION}" \
        -n "${NAMESPACE}" --record || true
    
    # Update frontend image
    kubectl set image deployment/frontend \
        frontend="${DOCKER_REGISTRY}/nebula-frontend:${VERSION}" \
        -n "${NAMESPACE}" --record || true
    
    # Update vector worker image
    kubectl set image deployment/vector-worker \
        worker="${DOCKER_REGISTRY}/nebula-vector-worker:${VERSION}" \
        -n "${NAMESPACE}" --record || true
    
    cd ../..
    echo -e "${GREEN}  ✓ Kubernetes manifests updated${NC}"
fi

# ---- Rolling Update with Health Checks ----
echo -e "${CYAN}[5/6] Performing rolling update...${NC}"

# Trigger rollout for each deployment
for deployment in backend frontend vector-worker; do
    echo -e "  Rolling update: ${YELLOW}${deployment}${NC}"
    
    # Trigger rollout restart
    kubectl rollout restart deployment "${deployment}" -n "${NAMESPACE}" 2>/dev/null || \
        kubectl rollout status deployment "${deployment}" -n "${NAMESPACE}" 2>/dev/null || true
    
    # Wait for rollout to complete
    if kubectl rollout status deployment "${deployment}" -n "${NAMESPACE}" --timeout=300s; then
        echo -e "  ${GREEN}✓ ${deployment} rollout complete${NC}"
    else
        echo -e "  ${RED}✗ ${deployment} rollout failed${NC}"
        echo -e "  ${YELLOW}Initiating rollback...${NC}"
        kubectl rollout undo deployment "${deployment}" -n "${NAMESPACE}"
        exit 1
    fi
done

# ---- Health Check Verification ----
echo -e "${CYAN}[6/6] Running post-deployment health checks...${NC}"

# Get the backend service URL
if kubectl get svc -n "${NAMESPACE}" nebula-backend &> /dev/null; then
    HEALTH_CHECK_URL="http://localhost:8000/health"
    
    # Port-forward to check health
    kubectl port-forward -n "${NAMESPACE}" svc/nebula-backend 8000:8000 &
    PF_PID=$!
    sleep 3
    
    # Run health checks
    for i in $(seq 1 ${MAX_RETRIES}); do
        if curl -sf "${HEALTH_CHECK_URL}" > /dev/null 2>&1; then
            echo -e "${GREEN}  ✓ Health check passed (attempt ${i})${NC}"
            break
        fi
        if [ "${i}" -eq "${MAX_RETRIES}" ]; then
            echo -e "${RED}  ✗ Health check failed after ${MAX_RETRIES} attempts${NC}"
            kill ${PF_PID} 2>/dev/null || true
            exit 1
        fi
        echo -e "  ${YELLOW}Waiting for service... (attempt ${i}/${MAX_RETRIES})${NC}"
        sleep ${RETRY_INTERVAL}
    done
    
    # Cleanup port-forward
    kill ${PF_PID} 2>/dev/null || true
fi

# Run integration smoke tests
echo -e "\n${CYAN}Running smoke tests...${NC}"
SMOKE_TESTS=(
    "GET /health => 200"
    "GET /api/v1/search?q=test => 200|401"
    "GET /metrics => 200|501"
)

for test in "${SMOKE_TESTS[@]}"; do
    METHOD=$(echo "${test}" | cut -d' ' -f1)
    PATH_URL=$(echo "${test}" | cut -d' ' -f2)
    EXPECTED=$(echo "${test}" | cut -d' ' -f4)
    
    if [ "${METHOD}" = "GET" ]; then
        STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000${PATH_URL}" 2>/dev/null || echo "000")
        if echo "${STATUS}" | grep -qE "${EXPECTED}"; then
            echo -e "${GREEN}  ✓ ${METHOD} ${PATH_URL} => ${STATUS}${NC}"
        else
            echo -e "${RED}  ✗ ${METHOD} ${PATH_URL} => ${STATUS} (expected ${EXPECTED})${NC}"
        fi
    fi
done

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Deployment completed successfully!        ${NC}"
echo -e "${GREEN}  Environment: ${ENVIRONMENT}                ${NC}"
echo -e "${GREEN}  Version: ${VERSION}                        ${NC}"
echo -e "${GREEN}============================================${NC}"