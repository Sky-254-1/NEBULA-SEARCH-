#!/bin/bash
set -euo pipefail

# Nebula Search Engine - Automated Rollback Script
# Supports Docker Compose and Kubernetes deployments with database restoration

# ============================================================
# Configuration
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${ROOT_DIR}/database/backups"
COMPOSE_FILE="${ROOT_DIR}/docker/docker-compose.yml"
PROD_COMPOSE="${ROOT_DIR}/docker-compose.prod.yml"

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
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

usage() {
    cat << EOF
Nebula Search Engine - Automated Rollback

Usage: $0 [options]

Options:
  --environment, -e     Target environment (production|staging|kubernetes)
  --revision, -r        Specific revision to rollback to (kubernetes only)
  --backup, -b          Backup file to restore from (docker-compose only)
  --skip-db             Skip database restoration
  --dry-run             Show what would be done without executing
  --help, -h            Show this help message

Examples:
  $0 --environment docker-compose --backup ./backups/postgres_20240101.sql.gz
  $0 --environment kubernetes --revision 5
  $0 --environment kubernetes (auto-detect previous revision)
  $0 --environment production --skip-db

EOF
    exit 0
}

# ============================================================
# Parse Arguments
# ============================================================
ENVIRONMENT=""
REVISION=""
BACKUP_FILE=""
SKIP_DB=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --environment|-e) ENVIRONMENT="$2"; shift 2 ;;
        --revision|-r) REVISION="$2"; shift 2 ;;
        --backup|-b) BACKUP_FILE="$2"; shift 2 ;;
        --skip-db) SKIP_DB=true; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        --help|-h) usage ;;
        *) log_error "Unknown option: $1"; usage ;;
    esac
done

if [ -z "$ENVIRONMENT" ]; then
    log_error "Environment is required. Use --environment or -e."
    usage
fi

# ============================================================
# Rollback: Docker Compose
# ============================================================
rollback_docker_compose() {
    log_info "Initiating Docker Compose rollback..."
    
    # Find and load backup
    if [ -z "$BACKUP_FILE" ]; then
        log_info "No backup specified. Finding latest backup..."
        BACKUP_FILE=$(ls -t "${BACKUP_DIR}"/nebula_*.sql* 2>/dev/null | head -1)
        
        if [ -z "$BACKUP_FILE" ]; then
            log_error "No backup found in ${BACKUP_DIR}. Use --backup to specify one."
            exit 1
        fi
        log_info "Using latest backup: $BACKUP_FILE"
    fi
    
    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would execute the following:"
        echo "  1. Stop current services"
        echo "  2. Restore database from: $BACKUP_FILE"
        echo "  3. Restart services with previous Docker images"
        echo "  4. Verify health"
        return 0
    fi
    
    # Record current state before rollback
    log_info "Recording current deployment state..."
    mkdir -p "${BACKUP_DIR}/rollback-records"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    docker ps --format "{{.Names}} {{.Image}} {{.Status}}" > "${BACKUP_DIR}/rollback-records/pre_rollback_${TIMESTAMP}.txt"
    
    # Step 1: Create emergency backup (if not already a backup being restored)
    PRE_BACKUP_NAME="pre_rollback_${TIMESTAMP}.sql.gz"
    log_info "Creating pre-rollback backup..."
    if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U nebula nebula | gzip > "${BACKUP_DIR}/${PRE_BACKUP_NAME}"; then
        log_success "Pre-rollback backup created: ${PRE_BACKUP_NAME}"
    else
        log_warn "Could not create emergency backup (postgres may not be running)"
    fi
    
    # Step 2: Restore database if not skipped
    if [ "$SKIP_DB" = false ]; then
        log_info "Restoring database from backup..."
        
        # Drop and recreate database
        log_info "Dropping and recreating database..."
        docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U nebula -c "DROP DATABASE IF EXISTS nebula;" 2>/dev/null || true
        docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U nebula -c "CREATE DATABASE nebula;" 2>/dev/null || true
        
        # Restore from backup
        if [[ "$BACKUP_FILE" == *.gz ]]; then
            gunzip -c "$BACKUP_FILE" | docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U nebula
        else
            cat "$BACKUP_FILE" | docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U nebula
        fi
        log_success "Database restored successfully"
    else
        log_info "Skipping database restoration"
    fi
    
    # Step 3: Pull previous Docker images (if available)
    log_info "Pulling previous Docker images..."
    docker compose -f "$COMPOSE_FILE" pull --ignore-pull-failures 2>/dev/null || true
    
    # Step 4: Redeploy services
    log_info "Redeploying services..."
    docker compose -f "$COMPOSE_FILE" up -d --force-recreate
    
    # Wait for services to be healthy
    log_info "Waiting for services to become healthy..."
    sleep 15
    
    # Step 5: Verify health
    log_info "Verifying service health..."
    for i in $(seq 1 12); do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            log_success "Health check passed"
            break
        fi
        if [ $i -eq 12 ]; then
            log_error "Health check failed after rollback"
            return 1
        fi
        sleep 5
    done
    
    log_success "Docker Compose rollback completed successfully"
    log_info "Services running:"
    docker compose -f "$COMPOSE_FILE" ps
}

# ============================================================
# Rollback: Kubernetes
# ============================================================
rollback_kubernetes() {
    log_info "Initiating Kubernetes rollback..."
    
    # Check for kubectl
    if ! command -v kubectl &>/dev/null; then
        log_error "kubectl is required for Kubernetes rollback"
        exit 1
    fi
    
    NAMESPACE="${K8S_NAMESPACE:-nebula}"
    DEPLOYMENTS=("nebula-backend" "nebula-frontend" "nebula-worker")
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would execute the following:"
        echo "  1. Get rollout history for deployments"
        echo "  2. Rollback to revision: ${REVISION:-previous}"
        echo "  3. Verify deployment status"
        return 0
    fi
    
    for DEPLOY in "${DEPLOYMENTS[@]}"; do
        log_info "Processing deployment: $DEPLOY"
        
        # Check if deployment exists
        if ! kubectl get deployment "$DEPLOY" -n "$NAMESPACE" &>/dev/null; then
            log_warn "Deployment $DEPLOY not found, skipping"
            continue
        fi
        
        # Get rollout history
        log_info "Rollout history for $DEPLOY:"
        kubectl rollout history deployment/"$DEPLOY" -n "$NAMESPACE" || true
        
        # Determine revision to rollback to
        ROLLBACK_REV="$REVISION"
        if [ -z "$ROLLBACK_REV" ]; then
            # Auto-detect previous revision
            ROLLBACK_REV=$(kubectl rollout history deployment/"$DEPLOY" -n "$NAMESPACE" 2>/dev/null | grep -v "REVISION" | tail -2 | head -1 | awk '{print $1}')
            if [ -z "$ROLLBACK_REV" ]; then
                log_warn "Could not detect previous revision for $DEPLOY, skipping"
                continue
            fi
        fi
        
        log_info "Rolling back $DEPLOY to revision $ROLLBACK_REV..."
        
        # Annotate with rollback metadata
        kubectl annotate deployment/"$DEPLOY" -n "$NAMESPACE" \
            rollback-timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
            rollback-revision="$ROLLBACK_REV" \
            --overwrite 2>/dev/null || true
        
        # Execute rollback
        kubectl rollout undo deployment/"$DEPLOY" -n "$NAMESPACE" \
            --to-revision="$ROLLBACK_REV"
        
        # Wait for rollback to complete
        log_info "Waiting for $DEPLOY rollback to complete..."
        if ! kubectl rollout status deployment/"$DEPLOY" -n "$NAMESPACE" --timeout=300s; then
            log_error "Rollback failed for $DEPLOY"
            return 1
        fi
        log_success "Rollback completed for $DEPLOY"
    done
    
    # Verify overall health
    log_info "Verifying Kubernetes health..."
    for i in $(seq 1 12); do
        READY_PODS=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=nebula-backend -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)
        if [ "$READY_PODS" == "True" ]; then
            log_success "All pods are ready"
            break
        fi
        if [ $i -eq 12 ]; then
            log_error "Pods failed to become ready after rollback"
            return 1
        fi
        sleep 5
    done
    
    log_success "Kubernetes rollback completed successfully"
    kubectl get pods -n "$NAMESPACE"
}

# ============================================================
# Rollback: Production (Full rollback with database)
# ============================================================
rollback_production() {
    log_info "Initiating full production rollback..."
    
    # Check for Docker
    if ! command -v docker &>/dev/null; then
        log_error "Docker is required for production rollback"
        exit 1
    fi
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    ROLLBACK_LOG="${BACKUP_DIR}/rollback-records/rollback_${TIMESTAMP}.log"
    mkdir -p "${BACKUP_DIR}/rollback-records"
    
    {
        echo "=== Rollback initiated at $(date) ==="
        echo "Environment: Production"
        echo "Backup: $BACKUP_FILE"
        echo "Skip DB: $SKIP_DB"
        echo ""
    } >> "$ROLLBACK_LOG"
    
    # Step 1: Create emergency snapshot
    log_info "Creating emergency database snapshot..."
    SNAPSHOT_FILE="${BACKUP_DIR}/emergency_${TIMESTAMP}.sql.gz"
    if docker compose exec -T postgres pg_dump -U nebula nebula 2>/dev/null | gzip > "$SNAPSHOT_FILE"; then
        log_success "Emergency snapshot created: $SNAPSHOT_FILE"
    else
        log_warn "Could not create emergency snapshot"
    fi
    
    # Step 2: Restore database if not skipped
    if [ "$SKIP_DB" = false ]; then
        log_info "Stopping backend services for database restore..."
        docker compose stop backend worker scheduler
        
        log_info "Restoring database..."
        docker compose exec -T postgres psql -U nebula -c "DROP DATABASE IF EXISTS nebula;" 2>/dev/null || true
        docker compose exec -T postgres psql -U nebula -c "CREATE DATABASE nebula;" 2>/dev/null || true
        
        if [[ "$BACKUP_FILE" == *.gz ]]; then
            gunzip -c "$BACKUP_FILE" | docker compose exec -T postgres psql -U nebula
        else
            cat "$BACKUP_FILE" | docker compose exec -T postgres psql -U nebula
        fi
        log_success "Database restored successfully"
    fi
    
    # Step 3: Restart services
    log_info "Restarting all services..."
    docker compose up -d --force-recreate
    
    # Step 4: Health verification
    log_info "Running health verification..."
    for i in $(seq 1 30); do
        HEALTH_STATUS=$(curl -sf http://localhost:8000/health 2>/dev/null || echo "failed")
        if [ "$HEALTH_STATUS" != "failed" ]; then
            log_success "Service health verified"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "Service health verification failed"
            log_info "Check logs with: docker compose logs --tail=50 backend"
            return 1
        fi
        sleep 5
    done
    
    log_success "Production rollback completed successfully"
    log_info "Rollback log saved to: $ROLLBACK_LOG"
}

# ============================================================
# Main Execution
# ============================================================
echo "======================================================"
echo -e "${CYAN}NEBULA SEARCH ENGINE - AUTOMATED ROLLBACK${NC}"
echo "======================================================"
echo "Started at: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

case "$ENVIRONMENT" in
    docker-compose|docker)
        rollback_docker_compose
        ;;
    kubernetes|k8s|kube)
        rollback_kubernetes
        ;;
    production|prod)
        rollback_production
        ;;
    staging)
        rollback_docker_compose
        ;;
    *)
        log_error "Unknown environment: $ENVIRONMENT"
        log_info "Supported: docker-compose, kubernetes, production, staging"
        exit 1
        ;;
esac

echo ""
echo "======================================================"
echo -e "${GREEN}ROLLBACK COMPLETED${NC}"
echo "Completed at: $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================================"