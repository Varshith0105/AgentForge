#!/bin/bash
# AgentForge Production Deployment Script

set -e

echo "=================================================="
echo "AgentForge Production Deployment"
echo "=================================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    log_warn "Running as root. Consider using a non-root user with sudo privileges."
fi

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    log_error ".env.production not found!"
    log_info "Please copy .env.production.example to .env.production and configure it."
    exit 1
fi

log_info "Environment file found"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi

log_info "Docker is installed"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

log_info "Docker Compose is installed"

# Pull latest images
log_info "Pulling latest Docker images..."
docker-compose -f docker-compose.prod.yml pull

# Build custom images
log_info "Building custom images..."
docker-compose -f docker-compose.prod.yml build

# Stop existing containers
log_info "Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Start services
log_info "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
log_info "Waiting for services to be healthy..."
sleep 10

# Check health
log_info "Checking service health..."

# Check PostgreSQL
if docker-compose -f docker-compose.prod.yml ps postgres | grep -q "Up"; then
    log_info "✓ PostgreSQL is running"
else
    log_error "✗ PostgreSQL is not running"
    exit 1
fi

# Check Redis
if docker-compose -f docker-compose.prod.yml ps redis | grep -q "Up"; then
    log_info "✓ Redis is running"
else
    log_error "✗ Redis is not running"
    exit 1
fi

# Check Qdrant
if docker-compose -f docker-compose.prod.yml ps qdrant | grep -q "Up"; then
    log_info "✓ Qdrant is running"
else
    log_error "✗ Qdrant is not running"
    exit 1
fi

# Check Backend
if docker-compose -f docker-compose.prod.yml ps backend | grep -q "Up"; then
    log_info "✓ Backend is running"
else
    log_error "✗ Backend is not running"
    exit 1
fi

# Check Backend health endpoint
log_info "Checking backend health endpoint..."
sleep 5

for i in {1..30}; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_info "✓ Backend health check passed"
        break
    else
        if [ $i -eq 30 ]; then
            log_error "✗ Backend health check failed after 30 attempts"
            docker-compose -f docker-compose.prod.yml logs backend
            exit 1
        fi
        log_info "Waiting for backend to be ready... ($i/30)"
        sleep 2
    fi
done

# Check Nginx
if docker-compose -f docker-compose.prod.yml ps nginx | grep -q "Up"; then
    log_info "✓ Nginx is running"
else
    log_error "✗ Nginx is not running"
    exit 1
fi

# Check Celery Worker
if docker-compose -f docker-compose.prod.yml ps celery_worker | grep -q "Up"; then
    log_info "✓ Celery Worker is running"
else
    log_warn "✗ Celery Worker is not running"
fi

# Display service URLs
echo ""
echo "=================================================="
log_info "Deployment successful!"
echo "=================================================="
echo ""
echo "Service URLs:"
echo "  Frontend:  http://localhost"
echo "  Backend:   http://localhost/api"
echo "  Health:    http://localhost/health"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose -f docker-compose.prod.yml down"
echo ""
echo "=================================================="
