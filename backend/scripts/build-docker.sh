#!/bin/bash
# Build Docker image for boloo-backend with chat fixes
# This script builds the Docker image locally and tags it for GitHub Container Registry

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🐳 Boloo Backend Docker Build Script${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Configuration
IMAGE_NAME="ghcr.io/diptendudip/boloo-backend"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
VERSION_TAG="${IMAGE_NAME}:v${TIMESTAMP}"
LATEST_TAG="${IMAGE_NAME}:latest"

# Get current directory (should be backend/)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}📂 Backend directory: ${BACKEND_DIR}${NC}"
echo -e "${YELLOW}🏷️  Version tag: v${TIMESTAMP}${NC}"
echo ""

# Navigate to backend directory
cd "$BACKEND_DIR"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Verify critical files exist
echo -e "${BLUE}🔍 Verifying files...${NC}"
required_files=(
    "Dockerfile"
    "requirements.txt"
    "app/main.py"
    "app/routers/chat.py"
    "app/utils/location_confirmation.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Missing required file: $file${NC}"
        exit 1
    fi
    echo -e "${GREEN}  ✓ $file${NC}"
done
echo ""

# Show chat fix verification
echo -e "${BLUE}🔧 Verifying chat fixes...${NC}"
if grep -q "bool(" app/utils/location_confirmation.py && \
   grep -q "bool(" app/routers/chat.py; then
    echo -e "${GREEN}  ✓ Chat fixes (bool wrappers) confirmed${NC}"
else
    echo -e "${YELLOW}  ⚠️  Warning: bool() wrappers not found in expected locations${NC}"
fi
echo ""

# Build Docker image
echo -e "${BLUE}🏗️  Building Docker image...${NC}"
echo -e "${YELLOW}This may take 3-5 minutes...${NC}"
echo ""

if docker build -t "$LATEST_TAG" -t "$VERSION_TAG" .; then
    echo ""
    echo -e "${GREEN}✅ Docker image built successfully!${NC}"
else
    echo ""
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Show image details
echo ""
echo -e "${BLUE}📦 Image Details:${NC}"
docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
echo ""

# Test image (quick validation)
echo -e "${BLUE}🧪 Running quick validation test...${NC}"
CONTAINER_ID=$(docker run -d --rm \
    -e DATABASE_URL="sqlite:///./test.db" \
    -e SECRET_KEY="test-secret-key-for-validation" \
    -e ANTHROPIC_API_KEY="test-key" \
    "$LATEST_TAG")

sleep 5

if docker ps | grep -q "$CONTAINER_ID"; then
    echo -e "${GREEN}✅ Container started successfully${NC}"
    docker stop "$CONTAINER_ID" > /dev/null 2>&1
else
    echo -e "${RED}❌ Container failed to start${NC}"
    docker logs "$CONTAINER_ID"
    exit 1
fi
echo ""

# Summary
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ BUILD SUCCESSFUL${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📌 Image Tags:${NC}"
echo -e "   ${GREEN}• ${LATEST_TAG}${NC}"
echo -e "   ${GREEN}• ${VERSION_TAG}${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo -e "   1. Test locally: ${BLUE}./scripts/test-docker.sh${NC}"
echo -e "   2. Push to registry: ${BLUE}./scripts/push-docker.sh${NC}"
echo ""
echo -e "${BLUE}💡 Manual Testing:${NC}"
echo -e "   ${BLUE}docker run -p 8000:8000 --env-file .env ${LATEST_TAG}${NC}"
echo ""
