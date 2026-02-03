#!/bin/bash
# Deploy Veritas to production
# Usage: ./scripts/deploy.sh [production|staging]

set -e

ENVIRONMENT=${1:-production}
echo "🚀 Deploying Veritas to $ENVIRONMENT..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found. Please create one from .env.example"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

# Validate required environment variables
if [ -z "$CDP_API_KEY_ID" ] || [ -z "$CDP_API_KEY_SECRET" ]; then
    echo "❌ Error: CDP API keys are required in .env file"
    exit 1
fi

# Build and start services
echo "📦 Building Docker images..."
docker compose -f docker-compose.yml build --no-cache

echo "🗄️  Starting databases..."
docker compose -f docker-compose.yml up -d postgres redis

# Wait for databases to be ready
echo "⏳ Waiting for databases..."
sleep 5

echo "🔧 Starting backend and frontend..."
docker compose -f docker-compose.yml up -d backend frontend

# Check health
echo "🏥 Checking service health..."
sleep 10

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend health check failed"
fi

if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "⚠️  Frontend health check failed"
fi

echo ""
echo "🎉 Deployment complete!"
echo "📱 Frontend: http://localhost:3000"
echo "🔌 API: http://localhost:8000"
echo ""
echo "📊 View logs: docker compose -f docker-compose.yml logs -f"
