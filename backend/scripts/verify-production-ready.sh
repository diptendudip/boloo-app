#!/bin/bash
# Production Readiness Verification Script
# Checks if the backend is ready for production deployment

set -e

echo "🔍 Boloo Backend - Production Readiness Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
ERRORS=0
WARNINGS=0

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
    ((ERRORS++))
}

warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    ((WARNINGS++))
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Change to backend directory
cd "$BACKEND_DIR"

echo "1️⃣  Checking Required Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

required_files=(
    "Dockerfile"
    "requirements.txt"
    ".dockerignore"
    "app/main.py"
    "app/config.py"
    ".env.example"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        success "$file exists"
    else
        error "$file is missing"
    fi
done

echo ""
echo "2️⃣  Checking Dockerfile Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check Dockerfile settings
if grep -q "WEB_CONCURRENCY" Dockerfile; then
    workers=$(grep "WEB_CONCURRENCY" Dockerfile | grep -o '[0-9]*' | tail -1)
    success "WEB_CONCURRENCY is set to $workers"
else
    warning "WEB_CONCURRENCY not found in Dockerfile"
fi

if grep -q "HEALTHCHECK" Dockerfile; then
    success "Health check is configured"
else
    error "Health check is missing"
fi

if grep -q "timeout" Dockerfile; then
    success "Timeout settings configured"
else
    warning "Timeout settings not found"
fi

if grep -q "max-requests" Dockerfile; then
    success "Worker recycling (max-requests) configured"
else
    warning "Worker recycling not configured - potential memory leaks"
fi

if grep -q "preload" Dockerfile; then
    success "Preload enabled for better memory efficiency"
else
    warning "Preload not enabled"
fi

echo ""
echo "3️⃣  Checking Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if all dependencies are pinned
unpinned=$(grep -v "^#" requirements.txt | grep -v "^$" | grep -v "==" | wc -l)
if [ "$unpinned" -eq 0 ]; then
    success "All dependencies are pinned"
else
    warning "$unpinned dependencies are not pinned"
fi

# Check for production essentials
essential_deps=(
    "fastapi"
    "uvicorn"
    "gunicorn"
    "sqlalchemy"
    "psycopg2-binary"
)

for dep in "${essential_deps[@]}"; do
    if grep -q "^$dep" requirements.txt; then
        success "$dep is included"
    else
        error "$dep is missing"
    fi
done

echo ""
echo "4️⃣  Checking .dockerignore"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f ".dockerignore" ]; then
    ignored_items=(
        "*.pyc"
        "__pycache__"
        ".git"
        "tests/"
        ".env"
        "venv/"
    )

    for item in "${ignored_items[@]}"; do
        if grep -q "$item" .dockerignore; then
            success "$item is excluded"
        else
            warning "$item not in .dockerignore - image will be larger"
        fi
    done
else
    error ".dockerignore is missing - Docker image will be unnecessarily large"
fi

echo ""
echo "5️⃣  Checking Configuration Security"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if .env file exists (should not in production)
if [ -f ".env" ]; then
    warning ".env file exists - ensure it's not committed to git"
else
    success "No .env file in repository (good for production)"
fi

# Check if .env.example exists
if [ -f ".env.example" ]; then
    success ".env.example template exists"
else
    warning ".env.example template is missing"
fi

# Check if .env.production.template exists
if [ -f ".env.production.template" ]; then
    success ".env.production.template exists"
else
    warning ".env.production.template is missing"
fi

# Check config.py for security validators
if grep -q "field_validator.*JWT_SECRET_KEY" app/config.py; then
    success "JWT secret validation is implemented"
else
    warning "JWT secret validation not found"
fi

echo ""
echo "6️⃣  Checking Documentation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docs=(
    "docs/PRODUCTION_DEPLOYMENT.md"
    "docs/DEPLOYMENT_PACKAGE.md"
)

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        success "$doc exists"
    else
        warning "$doc is missing"
    fi
done

echo ""
echo "7️⃣  Docker Build Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v docker &> /dev/null; then
    echo "🐳 Docker is available, testing build..."
    if docker build --quiet -t boloo-backend-test:verify . > /dev/null 2>&1; then
        success "Docker image builds successfully"

        # Get image size
        IMAGE_SIZE=$(docker images boloo-backend-test:verify --format "{{.Size}}")
        echo "   Image size: $IMAGE_SIZE"

        # Cleanup
        docker rmi boloo-backend-test:verify > /dev/null 2>&1
    else
        error "Docker build failed"
    fi
else
    warning "Docker not available, skipping build test"
fi

echo ""
echo "8️⃣  Calculating Package Sizes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Full directory size
FULL_SIZE=$(du -sh . | cut -f1)
echo "📊 Full directory size: $FULL_SIZE"

# Estimate deployable size (excluding common dev files)
DEPLOY_SIZE=$(du -sh --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='tests' --exclude='docs' --exclude='venv' --exclude='data' . 2>/dev/null | cut -f1 || echo "N/A")
echo "📦 Estimated deployment size: $DEPLOY_SIZE"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 VERIFICATION SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Backend is PRODUCTION READY.${NC}"
    EXIT_CODE=0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS warning(s) found. Review recommended.${NC}"
    EXIT_CODE=0
else
    echo -e "${RED}❌ $ERRORS error(s) and $WARNINGS warning(s) found.${NC}"
    echo -e "${RED}   Fix errors before deploying to production.${NC}"
    EXIT_CODE=1
fi

echo ""
echo "Next Steps:"
echo "  1. Create .env.production from .env.production.template"
echo "  2. Run: ./scripts/create-deployment-package.sh"
echo "  3. Review: docs/PRODUCTION_DEPLOYMENT.md"
echo "  4. Deploy using Docker or Azure CLI"
echo ""

exit $EXIT_CODE
