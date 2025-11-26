#!/bin/bash

# Manual Docker Deployment Script for Boloo Backend
# Usage: ./scripts/deploy-docker.sh [version] [environment]
# Example: ./scripts/deploy-docker.sh v1.0.0 production

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="ghcr.io"
IMAGE_NAME="diptendudip/boloo-backend"
AZURE_WEBAPP_NAME="boloo-backend-api"
RESOURCE_GROUP="boloo-production-rg"

# Get version from argument or generate timestamp-based version
VERSION="${1:-$(date +%Y.%m.%d-%H%M%S)}"
ENVIRONMENT="${2:-production}"

# Full image names
IMAGE_TAG="$REGISTRY/$IMAGE_NAME:$VERSION"
IMAGE_LATEST="$REGISTRY/$IMAGE_NAME:latest"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Boloo Backend Docker Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Version:${NC} $VERSION"
echo -e "${YELLOW}Environment:${NC} $ENVIRONMENT"
echo -e "${YELLOW}Image:${NC} $IMAGE_TAG"
echo ""

# Function to print step header
print_step() {
    echo ""
    echo -e "${BLUE}>>> $1${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Step 1: Check prerequisites
print_step "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_success "Docker is installed"

if ! command -v az &> /dev/null; then
    print_warning "Azure CLI is not installed. Skipping Azure checks."
    SKIP_AZURE=true
else
    print_success "Azure CLI is installed"
    SKIP_AZURE=false
fi

# Check if logged into Docker registry
print_step "Checking Docker registry authentication..."
if ! docker info | grep -q "Username"; then
    print_warning "Not logged into Docker registry. Attempting login..."
    echo "$GITHUB_TOKEN" | docker login $REGISTRY -u "$GITHUB_ACTOR" --password-stdin || {
        print_error "Failed to login to Docker registry"
        echo "Please run: docker login $REGISTRY"
        exit 1
    }
fi
print_success "Authenticated to Docker registry"

# Step 2: Build Docker image
print_step "Building Docker image..."

docker build \
    --tag "$IMAGE_TAG" \
    --tag "$IMAGE_LATEST" \
    --build-arg BUILDTIME="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
    --build-arg VERSION="$VERSION" \
    --build-arg REVISION="$(git rev-parse HEAD 2>/dev/null || echo 'unknown')" \
    --file Dockerfile \
    --platform linux/amd64 \
    . || {
    print_error "Docker build failed"
    exit 1
}

print_success "Docker image built successfully"

# Step 3: Tag image
print_step "Tagging Docker image..."

# Additional tags
docker tag "$IMAGE_TAG" "$REGISTRY/$IMAGE_NAME:$ENVIRONMENT"
docker tag "$IMAGE_TAG" "$REGISTRY/$IMAGE_NAME:$(date +%Y%m%d)"

print_success "Image tagged with multiple versions"

# Step 4: Push to registry
print_step "Pushing Docker image to registry..."

docker push "$IMAGE_TAG" || {
    print_error "Failed to push version tag"
    exit 1
}

docker push "$IMAGE_LATEST" || {
    print_error "Failed to push latest tag"
    exit 1
}

docker push "$REGISTRY/$IMAGE_NAME:$ENVIRONMENT" || {
    print_warning "Failed to push environment tag (non-critical)"
}

print_success "Docker images pushed to registry"

# Step 5: Deploy to Azure (if Azure CLI available)
if [ "$SKIP_AZURE" = false ]; then
    print_step "Deploying to Azure App Service..."

    # Check Azure login
    if ! az account show &> /dev/null; then
        print_warning "Not logged into Azure. Please run: az login"
        print_warning "Skipping Azure deployment"
    else
        # Set container image
        az webapp config container set \
            --name "$AZURE_WEBAPP_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --docker-custom-image-name "$IMAGE_TAG" \
            --docker-registry-server-url "https://$REGISTRY" || {
            print_error "Failed to update container configuration"
            exit 1
        }

        print_success "Container configuration updated"

        # Restart App Service
        print_step "Restarting Azure App Service..."
        az webapp restart \
            --name "$AZURE_WEBAPP_NAME" \
            --resource-group "$RESOURCE_GROUP" || {
            print_error "Failed to restart App Service"
            exit 1
        }

        print_success "App Service restarted"
    fi
else
    print_warning "Skipping Azure deployment (Azure CLI not available)"
fi

# Step 6: Wait for health check
print_step "Waiting for application to start..."
sleep 30

# Step 7: Health check
print_step "Running health check..."

HEALTH_URL="https://$AZURE_WEBAPP_NAME.azurewebsites.net/health"
MAX_RETRIES=10
RETRY_INTERVAL=15

for i in $(seq 1 $MAX_RETRIES); do
    echo -e "${YELLOW}Health check attempt $i/$MAX_RETRIES...${NC}"

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Health check passed!"
        echo ""
        echo -e "${GREEN}URL: $HEALTH_URL${NC}"
        echo -e "${GREEN}Response Code: $HTTP_CODE${NC}"
        HEALTH_PASSED=true
        break
    else
        print_warning "Health check failed with code: $HTTP_CODE"
        if [ $i -lt $MAX_RETRIES ]; then
            echo "Retrying in ${RETRY_INTERVAL}s..."
            sleep $RETRY_INTERVAL
        fi
        HEALTH_PASSED=false
    fi
done

if [ "$HEALTH_PASSED" = false ]; then
    print_error "Health check failed after $MAX_RETRIES attempts"
    print_warning "Application may still be starting. Check Azure portal for logs."
    exit 1
fi

# Step 8: Run smoke tests
print_step "Running smoke tests..."

BASE_URL="https://$AZURE_WEBAPP_NAME.azurewebsites.net"

# Test health endpoint
echo "Testing /health endpoint..."
if curl -f -s "$BASE_URL/health" > /dev/null; then
    print_success "/health endpoint OK"
else
    print_error "/health endpoint failed"
    exit 1
fi

# Test API documentation
echo "Testing /docs endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/docs")
if [ "$HTTP_CODE" = "200" ]; then
    print_success "/docs endpoint OK"
else
    print_error "/docs endpoint failed with code: $HTTP_CODE"
    exit 1
fi

# Step 9: Save deployment metadata
print_step "Saving deployment metadata..."

cat > "deployment-$VERSION.json" <<EOF
{
  "version": "$VERSION",
  "environment": "$ENVIRONMENT",
  "image": "$IMAGE_TAG",
  "timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "deployed_by": "$(whoami)",
  "health_check": "passed",
  "url": "$BASE_URL"
}
EOF

print_success "Deployment metadata saved to deployment-$VERSION.json"

# Final summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Deployment Completed Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Version:${NC} $VERSION"
echo -e "${YELLOW}Image:${NC} $IMAGE_TAG"
echo -e "${YELLOW}URL:${NC} $BASE_URL"
echo -e "${YELLOW}Health:${NC} ${GREEN}Passing${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  - Monitor logs: az webapp log tail --name $AZURE_WEBAPP_NAME --resource-group $RESOURCE_GROUP"
echo "  - View metrics: https://portal.azure.com"
echo "  - API docs: $BASE_URL/docs"
echo ""
