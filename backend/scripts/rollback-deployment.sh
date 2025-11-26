#!/bin/bash

# Docker Deployment Rollback Script for Boloo Backend
# Usage: ./scripts/rollback-deployment.sh [version]
# Example: ./scripts/rollback-deployment.sh v1.0.0
#          ./scripts/rollback-deployment.sh previous

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REGISTRY="ghcr.io"
IMAGE_NAME="diptendudip/boloo-backend"
AZURE_WEBAPP_NAME="boloo-backend-api"
RESOURCE_GROUP="boloo-production-rg"

echo -e "${RED}========================================${NC}"
echo -e "${RED}   Boloo Backend Deployment Rollback${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Function to print messages
print_step() {
    echo ""
    echo -e "${BLUE}>>> $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check prerequisites
print_step "Checking prerequisites..."

if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed"
    exit 1
fi

if ! az account show &> /dev/null; then
    print_error "Not logged into Azure. Please run: az login"
    exit 1
fi

print_success "Prerequisites checked"

# Get current deployment
print_step "Fetching current deployment information..."

CURRENT_IMAGE=$(az webapp config container show \
    --name "$AZURE_WEBAPP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query '[0].value' -o tsv 2>/dev/null || echo "unknown")

echo -e "${YELLOW}Current image:${NC} $CURRENT_IMAGE"

# List available images
print_step "Fetching available images..."

echo ""
echo "Available images from GitHub Container Registry:"
echo ""

# Fetch image tags using GitHub API (requires GITHUB_TOKEN)
if [ -n "${GITHUB_TOKEN:-}" ]; then
    AVAILABLE_TAGS=$(curl -s \
        -H "Authorization: Bearer $GITHUB_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/user/packages/container/boloo-backend/versions" | \
        jq -r '.[].metadata.container.tags[]' 2>/dev/null | sort -r | head -10 || echo "")

    if [ -n "$AVAILABLE_TAGS" ]; then
        echo "$AVAILABLE_TAGS" | nl
    else
        print_warning "Could not fetch available tags from GitHub"
        echo "Using Docker registry..."

        # Alternative: Use Docker to list tags
        AVAILABLE_TAGS=$(docker images "$REGISTRY/$IMAGE_NAME" --format "{{.Tag}}" | grep -v "buildcache" | sort -r | head -10 || echo "")

        if [ -n "$AVAILABLE_TAGS" ]; then
            echo "$AVAILABLE_TAGS" | nl
        else
            print_error "No available images found"
            exit 1
        fi
    fi
else
    print_warning "GITHUB_TOKEN not set. Checking local Docker images..."

    AVAILABLE_TAGS=$(docker images "$REGISTRY/$IMAGE_NAME" --format "{{.Tag}}" | grep -v "buildcache" | sort -r | head -10 || echo "")

    if [ -n "$AVAILABLE_TAGS" ]; then
        echo "$AVAILABLE_TAGS" | nl
    else
        print_error "No available images found locally"
        echo "Please set GITHUB_TOKEN or pull images first"
        exit 1
    fi
fi

echo ""

# Select version to rollback to
TARGET_VERSION="${1:-}"

if [ -z "$TARGET_VERSION" ]; then
    echo -e "${YELLOW}Enter the tag number or version to rollback to:${NC}"
    read -r SELECTION

    if [[ "$SELECTION" =~ ^[0-9]+$ ]]; then
        TARGET_VERSION=$(echo "$AVAILABLE_TAGS" | sed -n "${SELECTION}p")
    else
        TARGET_VERSION="$SELECTION"
    fi
fi

# Handle "previous" keyword
if [ "$TARGET_VERSION" = "previous" ]; then
    TARGET_VERSION=$(echo "$AVAILABLE_TAGS" | sed -n '2p')
    print_warning "Rolling back to previous version: $TARGET_VERSION"
fi

if [ -z "$TARGET_VERSION" ]; then
    print_error "No version specified for rollback"
    exit 1
fi

TARGET_IMAGE="$REGISTRY/$IMAGE_NAME:$TARGET_VERSION"

echo ""
echo -e "${RED}WARNING: You are about to rollback deployment${NC}"
echo -e "${YELLOW}From:${NC} $CURRENT_IMAGE"
echo -e "${YELLOW}To:${NC} $TARGET_IMAGE"
echo ""
echo -e "${YELLOW}This will:${NC}"
echo "  1. Update the container image in Azure App Service"
echo "  2. Restart the application"
echo "  3. Potentially cause brief downtime"
echo ""
echo -e "${RED}Are you sure you want to continue? (yes/no)${NC}"
read -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    print_warning "Rollback cancelled"
    exit 0
fi

# Create backup of current state
print_step "Creating backup of current deployment state..."

BACKUP_FILE="deployment-backup-$(date +%Y%m%d-%H%M%S).json"

az webapp config container show \
    --name "$AZURE_WEBAPP_NAME" \
    --resource-group "$RESOURCE_GROUP" > "$BACKUP_FILE" || {
    print_warning "Failed to create backup file"
}

print_success "Backup saved to $BACKUP_FILE"

# Perform rollback
print_step "Rolling back to $TARGET_VERSION..."

az webapp config container set \
    --name "$AZURE_WEBAPP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --docker-custom-image-name "$TARGET_IMAGE" || {
    print_error "Failed to update container image"
    print_warning "You can restore from backup: $BACKUP_FILE"
    exit 1
}

print_success "Container image updated"

# Restart App Service
print_step "Restarting Azure App Service..."

az webapp restart \
    --name "$AZURE_WEBAPP_NAME" \
    --resource-group "$RESOURCE_GROUP" || {
    print_error "Failed to restart App Service"
    exit 1
}

print_success "App Service restarted"

# Wait for restart
print_step "Waiting for application to start..."
sleep 30

# Health check
print_step "Running health check..."

HEALTH_URL="https://$AZURE_WEBAPP_NAME.azurewebsites.net/health"
MAX_RETRIES=10
RETRY_INTERVAL=15

for i in $(seq 1 $MAX_RETRIES); do
    echo -e "${YELLOW}Health check attempt $i/$MAX_RETRIES...${NC}"

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Health check passed!"
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
    echo ""
    echo -e "${RED}Rollback may have failed. Options:${NC}"
    echo "  1. Check logs: az webapp log tail --name $AZURE_WEBAPP_NAME --resource-group $RESOURCE_GROUP"
    echo "  2. Restore from backup: Use $BACKUP_FILE"
    echo "  3. Try different version: ./scripts/rollback-deployment.sh [version]"
    exit 1
fi

# Run smoke tests
print_step "Running smoke tests..."

BASE_URL="https://$AZURE_WEBAPP_NAME.azurewebsites.net"

echo "Testing /health endpoint..."
if curl -f -s "$BASE_URL/health" > /dev/null; then
    print_success "/health endpoint OK"
else
    print_error "/health endpoint failed"
    exit 1
fi

echo "Testing /docs endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/docs")
if [ "$HTTP_CODE" = "200" ]; then
    print_success "/docs endpoint OK"
else
    print_error "/docs endpoint failed with code: $HTTP_CODE"
fi

# Save rollback metadata
print_step "Saving rollback metadata..."

cat > "rollback-$(date +%Y%m%d-%H%M%S).json" <<EOF
{
  "timestamp": "$(date -u +'%Y-%m-%dT%H:%M:%SZ')",
  "from_image": "$CURRENT_IMAGE",
  "to_image": "$TARGET_IMAGE",
  "version": "$TARGET_VERSION",
  "performed_by": "$(whoami)",
  "backup_file": "$BACKUP_FILE",
  "health_check": "passed",
  "reason": "manual_rollback"
}
EOF

print_success "Rollback metadata saved"

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Rollback Completed Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Previous version:${NC} $CURRENT_IMAGE"
echo -e "${YELLOW}Current version:${NC} $TARGET_IMAGE"
echo -e "${YELLOW}Backup file:${NC} $BACKUP_FILE"
echo -e "${YELLOW}Health status:${NC} ${GREEN}Passing${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  - Monitor logs: az webapp log tail --name $AZURE_WEBAPP_NAME --resource-group $RESOURCE_GROUP"
echo "  - Test application: $BASE_URL/docs"
echo "  - Remove backup: rm $BACKUP_FILE (after confirming rollback success)"
echo ""
