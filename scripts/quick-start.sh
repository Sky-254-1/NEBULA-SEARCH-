#!/bin/bash
# Nebula Search - Quick Start Script
# Sets up and starts the development environment

set -e

echo "🚀 Nebula Search - Quick Start"
echo "================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Please install Docker Desktop."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed."; exit 1; }
echo "✅ Docker and Docker Compose found"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
fi

# Start services
echo "Starting services with Docker Compose..."
docker compose -f docker-compose.dev.yml up --build -d

echo ""
echo "Waiting for services to be ready..."
sleep 5

# Run database migrations
echo "Running database migrations..."
docker compose -f docker-compose.dev.yml exec -T backend alembic upgrade head || true

echo ""
echo "================================"
echo "✅ Development environment started!"
echo "================================"
echo ""
echo "Services running:"
echo "  📱 Frontend:  http://localhost:3000"
echo "  🔧 Backend:   http://localhost:8000"
echo "  📚 API Docs:  http://localhost:8000/docs"
echo "  🗄️  PostgreSQL: localhost:5432"
echo "  🔴 Redis:     localhost:6379"
echo "  🔍 Elasticsearch: http://localhost:9200"
echo "  📦 MinIO:     http://localhost:9000"
echo ""
echo "Useful commands:"
echo "  make logs          - View all logs"
echo "  make test          - Run all tests"
echo "  make shell         - Open backend shell"
echo "  make dev-down      - Stop services"
echo "  make help          - Show all commands"
echo ""
echo "To stop: make dev-down"