#!/bin/bash
set -euo pipefail

# Nebula Search Engine - Quick Start Deployment Script
# This script automates the initial production deployment

echo "==================================="
echo "Nebula Search Engine - Quick Start"
echo "==================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker installed: $(docker --version)${NC}"

# Check Docker Compose
if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose installed: $(docker compose version)${NC}"

# Check disk space
AVAILABLE_GB=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_GB" -lt 50 ]; then
    echo -e "${YELLOW}⚠ Warning: Less than 50GB disk space available${NC}"
fi

# Environment setup
echo ""
echo "Setting up environment..."

if [ ! -f .env.production ]; then
    if [ -f .env.example ]; then
        echo "Creating .env.production from template..."
        cp .env.example .env.production
        echo -e "${YELLOW}⚠ IMPORTANT: Edit .env.production and set secure passwords!${NC}"
        echo "  Required: POSTGRES_PASSWORD, JWT_SECRET, MINIO_ROOT_PASSWORD, GRAFANA_ADMIN_PASSWORD"
        echo ""
        read -p "Press Enter after editing .env.production..."
    else
        echo -e "${RED}✗ .env.example not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env.production exists${NC}"
fi

# SSL setup
echo ""
echo "Checking SSL certificates..."
mkdir -p docker/ssl/live/nebula-search

if [ ! -f docker/ssl/live/nebula-search/fullchain.pem ]; then
    echo -e "${YELLOW}⚠ SSL certificates not found${NC}"
    echo "Choose an option:"
    echo "  1) Generate self-signed certificate (development only)"
    echo "  2) Skip SSL setup (use HTTP only)"
    echo "  3) Exit and add certificates manually"
    read -p "Enter choice [1-3]: " ssl_choice
    
    case $ssl_choice in
        1)
            echo "Generating self-signed certificate..."
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout docker/ssl/live/nebula-search/privkey.pem \
                -out docker/ssl/live/nebula-search/fullchain.pem \
                -subj "/CN=localhost" \
                -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
            chmod 600 docker/ssl/live/nebula-search/privkey.pem
            echo -e "${GREEN}✓ Self-signed certificate generated${NC}"
            ;;
        2)
            echo -e "${YELLOW}⚠ Skipping SSL. Update nginx config to use HTTP only.${NC}"
            ;;
        3)
            echo "Exiting. Add SSL certificates to docker/ssl/live/nebula-search/"
            exit 0
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
else
    echo -e "${GREEN}✓ SSL certificates exist${NC}"
fi

# Create backup directory
echo ""
echo "Creating backup directory..."
mkdir -p backups
echo -e "${GREEN}✓ Backup directory created${NC}"

# Validate Docker Compose configuration
echo ""
echo "Validating Docker Compose configuration..."
if docker compose -f docker-compose.prod.yml config > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker Compose configuration valid${NC}"
else
    echo -e "${RED}✗ Docker Compose configuration invalid${NC}"
    docker compose -f docker-compose.prod.yml config
    exit 1
fi

# Build images
echo ""
echo "Building Docker images..."
docker compose -f docker-compose.prod.yml build --no-cache

# Start services
echo ""
echo "Starting services..."
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to start..."
sleep 10

# Check service status
echo ""
echo "Checking service status..."
docker compose -f docker-compose.prod.yml ps

# Health checks
echo ""
echo "Performing health checks..."

# Wait for backend to be ready
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf https://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is healthy${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for backend... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}✗ Backend health check failed${NC}"
    echo "Check logs: docker compose -f docker-compose.prod.yml logs backend"
    exit 1
fi

# Check PostgreSQL
if docker compose -f docker-compose.prod.yml exec -T postgres pg_isready -U nebula > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is healthy${NC}"
else
    echo -e "${RED}✗ PostgreSQL health check failed${NC}"
fi

# Check Redis
if docker compose -f docker-compose.prod.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is healthy${NC}"
else
    echo -e "${RED}✗ Redis health check failed${NC}"
fi

# Display access information
echo ""
echo "==================================="
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo "==================================="
echo ""
echo "Access URLs:"
echo "  Frontend: https://localhost (or your domain)"
echo "  API Docs: https://localhost/docs"
echo "  Backend:  http://localhost:8000"
echo "  Grafana:  http://localhost:3001"
echo "  Prometheus: http://localhost:9090"
echo ""
echo "Default Grafana credentials:"
echo "  Username: admin"
echo "  Password: (check .env.production)"
echo ""
echo "Next steps:"
echo "  1. Configure your domain in .env.production"
echo "  2. Set up SSL certificates (if not done)"
echo "  3. Configure automated backups in crontab"
echo "  4. Review monitoring dashboards in Grafana"
echo "  5. Test the application"
echo ""
echo "Useful commands:"
echo "  View logs:     docker compose -f docker-compose.prod.yml logs -f"
echo "  Stop services: docker compose -f docker-compose.prod.yml down"
echo "  Restart:       docker compose -f docker-compose.prod.yml restart"
echo "  Backup:        ./scripts/backup.sh all"
echo ""
echo -e "${YELLOW}⚠ Remember to:${NC}"
echo "  - Change default passwords in .env.production"
echo "  - Configure firewall rules (ports 80, 443, 22 only)"
echo "  - Set up monitoring alerts in Grafana"
echo "  - Test backup restoration procedures"
echo ""