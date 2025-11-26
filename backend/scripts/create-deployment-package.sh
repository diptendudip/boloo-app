#!/bin/bash
# Production Deployment Package Creator
# Creates an optimized deployment package for Boloo Backend

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
PACKAGE_DIR="$BACKEND_DIR/deploy-package"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
PACKAGE_NAME="boloo-backend-prod-$TIMESTAMP"

echo "🚀 Creating Production Deployment Package for Boloo Backend"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Clean previous package
if [ -d "$PACKAGE_DIR" ]; then
    echo "🧹 Cleaning previous package..."
    rm -rf "$PACKAGE_DIR"
fi

# Create package directory
echo "📁 Creating package directory..."
mkdir -p "$PACKAGE_DIR/$PACKAGE_NAME"

# Copy essential files
echo "📋 Copying production files..."
cd "$BACKEND_DIR"

# Copy application code
cp -r app "$PACKAGE_DIR/$PACKAGE_NAME/"
cp -r alembic "$PACKAGE_DIR/$PACKAGE_NAME/" 2>/dev/null || echo "⚠️  No alembic directory found"

# Copy configuration files
cp Dockerfile "$PACKAGE_DIR/$PACKAGE_NAME/"
cp requirements.txt "$PACKAGE_DIR/$PACKAGE_NAME/"
cp .dockerignore "$PACKAGE_DIR/$PACKAGE_NAME/"
cp alembic.ini "$PACKAGE_DIR/$PACKAGE_NAME/" 2>/dev/null || echo "⚠️  No alembic.ini found"

# Copy environment template (never copy actual .env)
cp .env.example "$PACKAGE_DIR/$PACKAGE_NAME/"

# Copy documentation
mkdir -p "$PACKAGE_DIR/$PACKAGE_NAME/docs"
cp docs/PRODUCTION_DEPLOYMENT.md "$PACKAGE_DIR/$PACKAGE_NAME/docs/" 2>/dev/null || echo "⚠️  No deployment docs found"
cp docs/DEPLOYMENT_PACKAGE.md "$PACKAGE_DIR/$PACKAGE_NAME/docs/" 2>/dev/null || echo "⚠️  No package docs found"
cp README*.md "$PACKAGE_DIR/$PACKAGE_NAME/" 2>/dev/null || echo "⚠️  No README found"

# Create deployment instructions
cat > "$PACKAGE_DIR/$PACKAGE_NAME/DEPLOY.md" << 'EOF'
# Quick Deployment Instructions

## Prerequisites
- Docker installed
- Azure CLI installed and logged in
- .env.production file configured

## Step 1: Build Docker Image
```bash
docker build -t boloo-backend:production .
```

## Step 2: Test Locally
```bash
# Create .env.production file first!
docker run -p 8000:8000 --env-file .env.production boloo-backend:production
```

## Step 3: Deploy to Azure

### Option A: Azure Container Registry + App Service
```bash
# Login to ACR
az acr login --name <your-registry>

# Tag and push
docker tag boloo-backend:production <your-registry>.azurecr.io/boloo-backend:latest
docker push <your-registry>.azurecr.io/boloo-backend:latest

# Deploy to App Service
az webapp config container set \
  --name boloo-backend \
  --resource-group boloo-rg \
  --docker-custom-image-name <your-registry>.azurecr.io/boloo-backend:latest \
  --docker-registry-server-url https://<your-registry>.azurecr.io
```

### Option B: Azure Web App (Direct)
```bash
az webapp up \
  --name boloo-backend \
  --resource-group boloo-rg \
  --runtime "PYTHON:3.11" \
  --sku B2
```

## Step 4: Configure Environment Variables
```bash
# Set environment variables in Azure
az webapp config appsettings set \
  --name boloo-backend \
  --resource-group boloo-rg \
  --settings \
    APP_ENV=production \
    DATABASE_URL="your-postgres-url" \
    AZURE_OPENAI_ENDPOINT="your-endpoint" \
    AZURE_OPENAI_API_KEY="your-key" \
    JWT_SECRET_KEY="your-secret"
```

## Step 5: Run Database Migrations
```bash
# Via Azure SSH console
alembic upgrade head
```

## Step 6: Verify Deployment
```bash
# Health check
curl https://boloo-backend.azurewebsites.net/health

# Test API
curl https://boloo-backend.azurewebsites.net/api/v1/docs
```

## Troubleshooting
See docs/PRODUCTION_DEPLOYMENT.md for detailed troubleshooting.

## Support
Email: diptendudip@gmail.com
EOF

# Calculate sizes
echo ""
echo "📊 Package Information:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PACKAGE_SIZE=$(du -sh "$PACKAGE_DIR/$PACKAGE_NAME" | cut -f1)
echo "Package size: $PACKAGE_SIZE"
echo "Package location: $PACKAGE_DIR/$PACKAGE_NAME"

# Create archive
echo ""
echo "📦 Creating compressed archive..."
cd "$PACKAGE_DIR"

# Create tar.gz archive
tar -czf "$PACKAGE_NAME.tar.gz" "$PACKAGE_NAME"
ARCHIVE_SIZE=$(du -sh "$PACKAGE_NAME.tar.gz" | cut -f1)

# Create zip archive (Windows-compatible)
zip -r -q "$PACKAGE_NAME.zip" "$PACKAGE_NAME"
ZIP_SIZE=$(du -sh "$PACKAGE_NAME.zip" | cut -f1)

echo "✅ Tar.gz archive created: $PACKAGE_NAME.tar.gz ($ARCHIVE_SIZE)"
echo "✅ Zip archive created: $PACKAGE_NAME.zip ($ZIP_SIZE)"

# Create checksum
echo ""
echo "🔐 Generating checksums..."
if command -v sha256sum &> /dev/null; then
    sha256sum "$PACKAGE_NAME.tar.gz" > "$PACKAGE_NAME.tar.gz.sha256"
    sha256sum "$PACKAGE_NAME.zip" > "$PACKAGE_NAME.zip.sha256"
    echo "✅ SHA256 checksums created"
elif command -v shasum &> /dev/null; then
    shasum -a 256 "$PACKAGE_NAME.tar.gz" > "$PACKAGE_NAME.tar.gz.sha256"
    shasum -a 256 "$PACKAGE_NAME.zip" > "$PACKAGE_NAME.zip.sha256"
    echo "✅ SHA256 checksums created"
fi

# Create deployment manifest
cat > "$PACKAGE_DIR/$PACKAGE_NAME-manifest.json" << EOF
{
  "package_name": "$PACKAGE_NAME",
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "version": "1.0.0",
  "target_users": 100,
  "recommended_tier": "Azure B2 (3.5GB RAM)",
  "workers": 2,
  "python_version": "3.11",
  "archives": {
    "tar_gz": {
      "filename": "$PACKAGE_NAME.tar.gz",
      "size": "$ARCHIVE_SIZE"
    },
    "zip": {
      "filename": "$PACKAGE_NAME.zip",
      "size": "$ZIP_SIZE"
    }
  },
  "deployment_docs": "DEPLOY.md",
  "full_docs": "docs/PRODUCTION_DEPLOYMENT.md"
}
EOF

echo "✅ Deployment manifest created"

# Summary
echo ""
echo "🎉 Deployment Package Created Successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📦 Package Details:"
echo "  Name: $PACKAGE_NAME"
echo "  Location: $PACKAGE_DIR/"
echo "  Archives:"
echo "    - $PACKAGE_NAME.tar.gz ($ARCHIVE_SIZE)"
echo "    - $PACKAGE_NAME.zip ($ZIP_SIZE)"
echo ""
echo "📋 Next Steps:"
echo "  1. Review DEPLOY.md for deployment instructions"
echo "  2. Configure .env.production with production secrets"
echo "  3. Run database migrations before deployment"
echo "  4. Deploy using Docker or Azure CLI"
echo ""
echo "📚 Documentation:"
echo "  - Quick Start: $PACKAGE_DIR/$PACKAGE_NAME/DEPLOY.md"
echo "  - Full Guide: $PACKAGE_DIR/$PACKAGE_NAME/docs/PRODUCTION_DEPLOYMENT.md"
echo ""
echo "✉️  Support: diptendudip@gmail.com"
echo ""
