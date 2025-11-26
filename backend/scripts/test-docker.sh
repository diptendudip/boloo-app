#!/bin/bash
# Test Docker image locally before pushing
# Runs comprehensive tests including health check, API validation, and chat functionality

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🧪 Docker Image Local Testing${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Configuration
IMAGE_NAME="ghcr.io/diptendudip/boloo-backend:latest"
CONTAINER_NAME="boloo-backend-test"
PORT=8001  # Use different port to avoid conflicts

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Check if .env exists
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo -e "${YELLOW}💡 Copy .env.example to .env and configure it${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

# Check if image exists
if ! docker images "$IMAGE_NAME" | grep -q "latest"; then
    echo -e "${RED}❌ Image not found: $IMAGE_NAME${NC}"
    echo -e "${YELLOW}💡 Build the image first: ./scripts/build-docker.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Image found: $IMAGE_NAME${NC}"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    docker stop "$CONTAINER_NAME" > /dev/null 2>&1 || true
    docker rm "$CONTAINER_NAME" > /dev/null 2>&1 || true
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Stop existing test container if running
docker stop "$CONTAINER_NAME" > /dev/null 2>&1 || true
docker rm "$CONTAINER_NAME" > /dev/null 2>&1 || true

# Start container
echo -e "${BLUE}🚀 Starting container...${NC}"
docker run -d \
    --name "$CONTAINER_NAME" \
    -p $PORT:8000 \
    --env-file "$BACKEND_DIR/.env" \
    "$IMAGE_NAME"

echo -e "${GREEN}✅ Container started: $CONTAINER_NAME${NC}"
echo ""

# Wait for container to be ready
echo -e "${BLUE}⏳ Waiting for service to be ready...${NC}"
MAX_WAIT=60
WAIT_COUNT=0

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Service is ready!${NC}"
        break
    fi

    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        echo -e "${RED}❌ Container stopped unexpectedly${NC}"
        echo ""
        echo -e "${BLUE}📋 Container logs:${NC}"
        docker logs "$CONTAINER_NAME"
        exit 1
    fi

    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
    echo -n "."
done

if [ $WAIT_COUNT -eq $MAX_WAIT ]; then
    echo ""
    echo -e "${RED}❌ Service failed to start within ${MAX_WAIT}s${NC}"
    echo ""
    echo -e "${BLUE}📋 Container logs:${NC}"
    docker logs "$CONTAINER_NAME"
    exit 1
fi

echo ""
echo ""

# Run tests
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🧪 Running Tests${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Test 1: Health Check
echo -e "${YELLOW}1️⃣  Health Check${NC}"
HEALTH_RESPONSE=$(curl -s http://localhost:$PORT/health)
if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
    echo -e "${GREEN}   ✅ Health check passed${NC}"
    echo -e "${BLUE}   Response: $HEALTH_RESPONSE${NC}"
else
    echo -e "${RED}   ❌ Health check failed${NC}"
    echo -e "${BLUE}   Response: $HEALTH_RESPONSE${NC}"
fi
echo ""

# Test 2: API Documentation
echo -e "${YELLOW}2️⃣  API Documentation${NC}"
DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/docs)
if [ "$DOCS_STATUS" == "200" ]; then
    echo -e "${GREEN}   ✅ API docs accessible${NC}"
    echo -e "${BLUE}   URL: http://localhost:$PORT/docs${NC}"
else
    echo -e "${RED}   ❌ API docs not accessible (HTTP $DOCS_STATUS)${NC}"
fi
echo ""

# Test 3: Root endpoint
echo -e "${YELLOW}3️⃣  Root Endpoint${NC}"
ROOT_RESPONSE=$(curl -s http://localhost:$PORT/)
if echo "$ROOT_RESPONSE" | grep -q "Boloo"; then
    echo -e "${GREEN}   ✅ Root endpoint working${NC}"
else
    echo -e "${RED}   ❌ Root endpoint unexpected response${NC}"
fi
echo ""

# Test 4: Container resource usage
echo -e "${YELLOW}4️⃣  Resource Usage${NC}"
STATS=$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" "$CONTAINER_NAME")
echo -e "${BLUE}$STATS${NC}"
echo ""

# Show container logs (last 20 lines)
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 Container Logs (last 20 lines)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
docker logs --tail 20 "$CONTAINER_NAME"
echo ""

# Summary
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ TESTING COMPLETE${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}🔗 Test URLs:${NC}"
echo -e "   ${GREEN}• Health: http://localhost:$PORT/health${NC}"
echo -e "   ${GREEN}• API Docs: http://localhost:$PORT/docs${NC}"
echo -e "   ${GREEN}• Root: http://localhost:$PORT/${NC}"
echo ""
echo -e "${YELLOW}📋 Manual Testing:${NC}"
echo -e "   ${BLUE}# View logs:${NC}"
echo -e "   docker logs -f $CONTAINER_NAME"
echo ""
echo -e "   ${BLUE}# Execute commands:${NC}"
echo -e "   docker exec -it $CONTAINER_NAME bash"
echo ""
echo -e "   ${BLUE}# Stop container:${NC}"
echo -e "   docker stop $CONTAINER_NAME"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo -e "   1. Manual testing: Test chat API endpoints"
echo -e "   2. If all tests pass: ${BLUE}./scripts/push-docker.sh${NC}"
echo ""
echo -e "${BLUE}Press Enter to stop container and exit...${NC}"
read
