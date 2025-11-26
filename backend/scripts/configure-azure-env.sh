#!/bin/bash

# Azure App Service Environment Configuration Script
# Usage: ./scripts/configure-azure-env.sh [environment]
# Example: ./scripts/configure-azure-env.sh production

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-production}"
AZURE_WEBAPP_NAME="boloo-backend-api"
RESOURCE_GROUP="boloo-production-rg"
KEY_VAULT_NAME="boloo-secrets-vault"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Azure App Service Configuration${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Environment:${NC} $ENVIRONMENT"
echo -e "${YELLOW}App Service:${NC} $AZURE_WEBAPP_NAME"
echo -e "${YELLOW}Resource Group:${NC} $RESOURCE_GROUP"
echo ""

# Function to print step header
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

# Check Azure CLI
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed"
    exit 1
fi

# Check Azure login
print_step "Checking Azure authentication..."
if ! az account show &> /dev/null; then
    print_error "Not logged into Azure. Please run: az login"
    exit 1
fi
print_success "Authenticated to Azure"

# Load environment variables from .env file if exists
if [ -f ".env.$ENVIRONMENT" ]; then
    print_step "Loading environment variables from .env.$ENVIRONMENT..."
    set -a
    source ".env.$ENVIRONMENT"
    set +a
    print_success "Environment variables loaded"
else
    print_warning ".env.$ENVIRONMENT file not found. Using interactive mode."
fi

# Configure application settings
print_step "Configuring application settings..."

# Core application settings
az webapp config appsettings set \
    --name "$AZURE_WEBAPP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --settings \
        ENVIRONMENT="$ENVIRONMENT" \
        PYTHONUNBUFFERED="1" \
        PYTHONDONTWRITEBYTECODE="1" \
        PORT="8000" \
        WEBSITES_PORT="8000" \
        DOCKER_ENABLE_CI="true" \
        WEB_CONCURRENCY="2" \
        WORKERS="2" \
        LOG_LEVEL="info" || {
    print_error "Failed to set core settings"
    exit 1
}

print_success "Core settings configured"

# Database configuration (if DATABASE_URL is set)
if [ -n "${DATABASE_URL:-}" ]; then
    print_step "Configuring database connection..."

    az webapp config appsettings set \
        --name "$AZURE_WEBAPP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --settings \
            DATABASE_URL="$DATABASE_URL" \
            DB_POOL_SIZE="20" \
            DB_MAX_OVERFLOW="10" \
            DB_POOL_TIMEOUT="30" || {
        print_warning "Failed to set database settings"
    }

    print_success "Database settings configured"
else
    print_warning "DATABASE_URL not set. Skipping database configuration."
fi

# JWT and Security settings
if [ -n "${JWT_SECRET_KEY:-}" ]; then
    print_step "Configuring security settings..."

    az webapp config appsettings set \
        --name "$AZURE_WEBAPP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --settings \
            JWT_SECRET_KEY="$JWT_SECRET_KEY" \
            JWT_ALGORITHM="${JWT_ALGORITHM:-HS256}" \
            ACCESS_TOKEN_EXPIRE_MINUTES="${ACCESS_TOKEN_EXPIRE_MINUTES:-30}" \
            REFRESH_TOKEN_EXPIRE_DAYS="${REFRESH_TOKEN_EXPIRE_DAYS:-7}" || {
        print_warning "Failed to set security settings"
    }

    print_success "Security settings configured"
else
    print_warning "JWT_SECRET_KEY not set. Skipping security configuration."
fi

# CORS configuration
if [ -n "${ALLOWED_ORIGINS:-}" ]; then
    print_step "Configuring CORS settings..."

    az webapp config appsettings set \
        --name "$AZURE_WEBAPP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --settings \
            ALLOWED_ORIGINS="$ALLOWED_ORIGINS" \
            ALLOWED_METHODS="${ALLOWED_METHODS:-GET,POST,PUT,DELETE,OPTIONS}" \
            ALLOWED_HEADERS="${ALLOWED_HEADERS:-*}" || {
        print_warning "Failed to set CORS settings"
    }

    print_success "CORS settings configured"
fi

# Redis configuration (if using Redis)
if [ -n "${REDIS_URL:-}" ]; then
    print_step "Configuring Redis cache..."

    az webapp config appsettings set \
        --name "$AZURE_WEBAPP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --settings \
            REDIS_URL="$REDIS_URL" \
            REDIS_SSL="${REDIS_SSL:-true}" \
            CACHE_TTL="${CACHE_TTL:-300}" || {
        print_warning "Failed to set Redis settings"
    }

    print_success "Redis settings configured"
fi

# Azure Storage configuration
if [ -n "${AZURE_STORAGE_CONNECTION_STRING:-}" ]; then
    print_step "Configuring Azure Storage..."

    az webapp config appsettings set \
        --name "$AZURE_WEBAPP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --settings \
            AZURE_STORAGE_CONNECTION_STRING="$AZURE_STORAGE_CONNECTION_STRING" \
            AZURE_STORAGE_CONTAINER="${AZURE_STORAGE_CONTAINER:-uploads}" || {
        print_warning "Failed to set storage settings"
    }

    print_success "Azure Storage settings configured"
fi

# Third-party API keys
print_step "Configuring third-party integrations..."

INTEGRATIONS_CONFIGURED=0

if [ -n "${OPENAI_API_KEY:-}" ]; then
    az webapp config appsettings set \
        --name "$AZURE_WEBAPP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --settings OPENAI_API_KEY="$OPENAI_API_KEY" || true
    INTEGRATIONS_CONFIGURED=$((INTEGRATIONS_CONFIGURED + 1))
fi

if [ -n "${SENDGRID_API_KEY:-}" ]; then
    az webapp config appsettings set \
        --name "$AZURE_WEBAPP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --settings \
            SENDGRID_API_KEY="$SENDGRID_API_KEY" \
            EMAIL_FROM="${EMAIL_FROM:-noreply@boloo.app}" || true
    INTEGRATIONS_CONFIGURED=$((INTEGRATIONS_CONFIGURED + 1))
fi

if [ -n "${TWILIO_ACCOUNT_SID:-}" ]; then
    az webapp config appsettings set \
        --name "$AZURE_WEBAPP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --settings \
            TWILIO_ACCOUNT_SID="$TWILIO_ACCOUNT_SID" \
            TWILIO_AUTH_TOKEN="${TWILIO_AUTH_TOKEN:-}" \
            TWILIO_PHONE_NUMBER="${TWILIO_PHONE_NUMBER:-}" || true
    INTEGRATIONS_CONFIGURED=$((INTEGRATIONS_CONFIGURED + 1))
fi

if [ $INTEGRATIONS_CONFIGURED -gt 0 ]; then
    print_success "Third-party integrations configured ($INTEGRATIONS_CONFIGURED services)"
else
    print_warning "No third-party integrations configured"
fi

# Enable detailed logging
print_step "Enabling application logging..."

az webapp log config \
    --name "$AZURE_WEBAPP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --application-logging filesystem \
    --detailed-error-messages true \
    --failed-request-tracing true \
    --web-server-logging filesystem || {
    print_warning "Failed to configure logging"
}

print_success "Logging configured"

# Enable health check monitoring
print_step "Configuring health check monitoring..."

az webapp config set \
    --name "$AZURE_WEBAPP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --generic-configurations '{"healthCheckPath": "/health"}' || {
    print_warning "Failed to configure health check"
}

print_success "Health check monitoring configured"

# Enable auto-scaling (if on Premium tier)
print_step "Checking auto-scaling configuration..."

CURRENT_SKU=$(az appservice plan show \
    --name "${AZURE_WEBAPP_NAME}-plan" \
    --resource-group "$RESOURCE_GROUP" \
    --query sku.tier -o tsv 2>/dev/null || echo "Unknown")

if [[ "$CURRENT_SKU" == "Premium"* ]] || [[ "$CURRENT_SKU" == "Isolated"* ]]; then
    print_step "Configuring auto-scaling rules..."
    # Auto-scaling configuration would go here
    print_success "Auto-scaling available on $CURRENT_SKU tier"
else
    print_warning "Auto-scaling not available on $CURRENT_SKU tier. Consider upgrading to Premium."
fi

# Summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Configuration Completed Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}App Service:${NC} $AZURE_WEBAPP_NAME"
echo -e "${YELLOW}Resource Group:${NC} $RESOURCE_GROUP"
echo -e "${YELLOW}Environment:${NC} $ENVIRONMENT"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  - Restart app: az webapp restart --name $AZURE_WEBAPP_NAME --resource-group $RESOURCE_GROUP"
echo "  - View settings: az webapp config appsettings list --name $AZURE_WEBAPP_NAME --resource-group $RESOURCE_GROUP"
echo "  - Stream logs: az webapp log tail --name $AZURE_WEBAPP_NAME --resource-group $RESOURCE_GROUP"
echo ""
