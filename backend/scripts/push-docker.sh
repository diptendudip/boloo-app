#!/bin/bash
# Push Docker image to GitHub Container Registry
# Requires: Docker login to ghcr.io with GitHub Personal Access Token

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 Push Docker Image to GitHub Container Registry${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Configuration
IMAGE_NAME="ghcr.io/diptendudip/boloo-backend"
LATEST_TAG="${IMAGE_NAME}:latest"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

# Check if image exists
if ! docker images "$IMAGE_NAME" | grep -q "latest"; then
    echo -e "${RED}❌ Image not found: $LATEST_TAG${NC}"
    echo -e "${YELLOW}💡 Build the image first: ./scripts/build-docker.sh${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Image found: $LATEST_TAG${NC}"
echo ""

# Check authentication
echo -e "${BLUE}🔐 Checking GitHub Container Registry authentication...${NC}"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}AUTHENTICATION REQUIRED${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}To push to GitHub Container Registry, you need:${NC}"
echo ""
echo -e "  1. ${BLUE}GitHub Personal Access Token (PAT)${NC} with permissions:"
echo -e "     • ${GREEN}write:packages${NC}"
echo -e "     • ${GREEN}read:packages${NC}"
echo -e "     • ${GREEN}delete:packages${NC} (optional)"
echo ""
echo -e "  2. ${BLUE}Create PAT at:${NC}"
echo -e "     ${BLUE}https://github.com/settings/tokens/new${NC}"
echo ""
echo -e "  3. ${BLUE}Login to GitHub Container Registry:${NC}"
echo -e "     ${GREEN}export CR_PAT=YOUR_TOKEN${NC}"
echo -e "     ${GREEN}echo \$CR_PAT | docker login ghcr.io -u diptendudip --password-stdin${NC}"
echo ""
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Prompt user
read -p "$(echo -e ${BLUE}'Have you logged in to ghcr.io? (y/n): '${NC})" -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}📝 Quick Login Steps:${NC}"
    echo ""
    echo -e "  ${GREEN}# 1. Set your GitHub PAT${NC}"
    echo -e "  export CR_PAT=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    echo ""
    echo -e "  ${GREEN}# 2. Login to GitHub Container Registry${NC}"
    echo -e "  echo \$CR_PAT | docker login ghcr.io -u diptendudip --password-stdin"
    echo ""
    echo -e "  ${GREEN}# 3. Run this script again${NC}"
    echo -e "  ./scripts/push-docker.sh"
    echo ""
    exit 0
fi

# Push all tags
echo ""
echo -e "${BLUE}🚀 Pushing images to GitHub Container Registry...${NC}"
echo ""

# Get all tags for the image
TAGS=$(docker images "$IMAGE_NAME" --format "{{.Tag}}" | grep -v "<none>")

for tag in $TAGS; do
    FULL_TAG="${IMAGE_NAME}:${tag}"
    echo -e "${YELLOW}📤 Pushing: ${FULL_TAG}${NC}"

    if docker push "$FULL_TAG"; then
        echo -e "${GREEN}✅ Pushed: ${tag}${NC}"
    else
        echo -e "${RED}❌ Failed to push: ${tag}${NC}"
        echo ""
        echo -e "${YELLOW}💡 Troubleshooting:${NC}"
        echo -e "  • Check your GitHub PAT has write:packages permission"
        echo -e "  • Verify you're logged in: ${BLUE}docker login ghcr.io${NC}"
        echo -e "  • Check repository permissions on GitHub"
        exit 1
    fi
    echo ""
done

# Summary
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ PUSH SUCCESSFUL${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📦 Pushed Images:${NC}"
for tag in $TAGS; do
    echo -e "   ${GREEN}• ${IMAGE_NAME}:${tag}${NC}"
done
echo ""
echo -e "${BLUE}🔗 View on GitHub:${NC}"
echo -e "   ${BLUE}https://github.com/diptendudip/boloo-backend/pkgs/container/boloo-backend${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo -e "   1. Update Azure deployment with new image"
echo -e "   2. Monitor deployment: ${BLUE}az webapp log tail --name boloo-backend --resource-group boloo-rg${NC}"
echo -e "   3. Test production: ${BLUE}curl https://boloo-backend.azurewebsites.net/health${NC}"
echo ""
