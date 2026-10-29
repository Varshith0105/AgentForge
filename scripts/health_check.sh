#!/bin/bash
# AgentForge Health Check Script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="${1:-http://localhost}"

echo "=================================================="
echo "AgentForge Health Check"
echo "=================================================="
echo "Base URL: $BASE_URL"
echo ""

# Function to check endpoint
check_endpoint() {
    local endpoint=$1
    local expected_status=${2:-200}
    local description=$3
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint" 2>/dev/null || echo "000")
    
    if [ "$response" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓${NC} $description (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗${NC} $description (HTTP $response, expected $expected_status)"
        return 1
    fi
}

# Check if services are running
echo "${BLUE}Checking Docker Services...${NC}"
if command -v docker-compose &> /dev/null; then
    if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
        echo -e "${GREEN}✓${NC} Docker services are running"
    else
        echo -e "${RED}✗${NC} Docker services are not running"
        echo "Run: docker-compose -f docker-compose.prod.yml up -d"
        exit 1
    fi
else
    echo -e "${YELLOW}!${NC} Docker Compose not found, skipping container check"
fi

echo ""
echo "${BLUE}Checking Endpoints...${NC}"

# Track failures
failures=0

# Health endpoints
check_endpoint "/health" 200 "Basic health check" || ((failures++))
check_endpoint "/ai-os-info" 200 "AI OS info" || ((failures++))

# API endpoints (expect 401 without auth)
check_endpoint "/api/v1/projects" 401 "Projects API" || ((failures++))
check_endpoint "/api/v1/mcp/servers" 401 "MCP servers API" || ((failures++))
check_endpoint "/api/v1/knowledge-engine/projects/1/memory" 401 "Knowledge engine API" || ((failures++))
check_endpoint "/api/v1/costs/summary" 401 "Cost tracking API" || ((failures++))
check_endpoint "/api/v1/git/1/status" 401 "Git operations API" || ((failures++))
check_endpoint "/api/v1/terminal/execute" 401 "Terminal API" || ((failures++))
check_endpoint "/api/v1/observability/metrics" 401 "Observability API" || ((failures++))

# Static files
check_endpoint "/" 200 "Frontend index" || ((failures++))
check_endpoint "/workspace.html" 200 "Workspace page" || ((failures++))

echo ""
echo "=================================================="

if [ $failures -eq 0 ]; then
    echo -e "${GREEN}All health checks passed!${NC}"
    exit 0
else
    echo -e "${RED}$failures health check(s) failed!${NC}"
    exit 1
fi
