# Azure Deployment Guide - Bultoo App

## Overview
This guide covers deploying the Bultoo app (FastAPI backend + PostgreSQL) to Azure using available credits.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Azure Resources Setup](#azure-resources-setup)
3. [Database Configuration](#database-configuration)
4. [Backend Deployment](#backend-deployment)
5. [Storage Setup](#storage-setup)
6. [CDN Configuration](#cdn-configuration)
7. [Cost Estimation](#cost-estimation)

---

## Prerequisites

### Required Tools
```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Set default subscription (if you have multiple)
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Install Azure Functions Core Tools (optional)
npm install -g azure-functions-core-tools@4
```

### Environment Variables
Create `.env.production` in your backend:
```bash
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/bultoo_db?sslmode=require
AZURE_STORAGE_CONNECTION_STRING=your_storage_connection_string
AZURE_STORAGE_CONTAINER=media
AZURE_CDN_ENDPOINT=https://bultoo.azureedge.net
CORS_ORIGINS=https://bultoo.com,https://www.bultoo.com
SECRET_KEY=your_secret_key_here
```

---

## Azure Resources Setup

### 1. Create Resource Group
```bash
# Create resource group in East US (change region as needed)
az group create \
  --name bultoo-rg \
  --location eastus

# Verify creation
az group show --name bultoo-rg
```

### 2. Create App Service Plan
```bash
# Create Linux App Service Plan (Free tier F1 for testing)
az appservice plan create \
  --name bultoo-plan \
  --resource-group bultoo-rg \
  --sku F1 \
  --is-linux

# For production, use B1 (Basic) or S1 (Standard)
# az appservice plan create \
#   --name bultoo-plan \
#   --resource-group bultoo-rg \
#   --sku B1 \
#   --is-linux
```

### 3. Create Web App for Backend
```bash
# Create Web App with Python 3.11 runtime
az webapp create \
  --resource-group bultoo-rg \
  --plan bultoo-plan \
  --name bultoo-api \
  --runtime "PYTHON:3.11"

# Enable HTTPS only
az webapp update \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --https-only true

# Get default hostname
az webapp show \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --query defaultHostName -o tsv
# Output: bultoo-api.azurewebsites.net
```

---

## Database Configuration

### 1. Create PostgreSQL Server
```bash
# Create PostgreSQL Flexible Server (Free tier available)
az postgres flexible-server create \
  --resource-group bultoo-rg \
  --name bultoo-db-server \
  --location eastus \
  --admin-user bultoo_admin \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 15 \
  --public-access 0.0.0.0-255.255.255.255

# Note: For production, restrict public-access to specific IPs
```

### 2. Create Database
```bash
# Create database
az postgres flexible-server db create \
  --resource-group bultoo-rg \
  --server-name bultoo-db-server \
  --database-name bultoo_db

# Get connection string
az postgres flexible-server show-connection-string \
  --server-name bultoo-db-server \
  --database-name bultoo_db \
  --admin-user bultoo_admin \
  --admin-password "YourSecurePassword123!"
```

### 3. Configure Firewall Rules
```bash
# Allow Azure services
az postgres flexible-server firewall-rule create \
  --resource-group bultoo-rg \
  --name bultoo-db-server \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# Add your local IP for development
az postgres flexible-server firewall-rule create \
  --resource-group bultoo-rg \
  --name bultoo-db-server \
  --rule-name AllowMyIP \
  --start-ip-address YOUR_IP \
  --end-ip-address YOUR_IP
```

### 4. Run Database Migrations
```bash
# From your local machine with database access
export DATABASE_URL="postgresql://bultoo_admin:YourSecurePassword123!@bultoo-db-server.postgres.database.azure.com:5432/bultoo_db?sslmode=require"

# If using Alembic
alembic upgrade head

# If using custom migration scripts
python manage.py migrate
```

---

## Backend Deployment

### 1. Prepare Application for Deployment

Create `startup.sh` in your backend root:
```bash
#!/bin/bash
set -e

# Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000 --timeout 600
```

Update `requirements.txt` to include:
```txt
fastapi
uvicorn[standard]
gunicorn
psycopg2-binary
sqlalchemy
alembic
python-dotenv
azure-storage-blob
azure-identity
pydantic
pydantic-settings
python-multipart
```

### 2. Configure Web App Settings
```bash
# Set Python version and startup command
az webapp config set \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --startup-file "startup.sh"

# Configure environment variables
az webapp config appsettings set \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --settings \
    DATABASE_URL="postgresql://bultoo_admin:YourSecurePassword123!@bultoo-db-server.postgres.database.azure.com:5432/bultoo_db?sslmode=require" \
    SECRET_KEY="your-secret-key-here" \
    CORS_ORIGINS="https://bultoo.com,https://www.bultoo.com" \
    ENVIRONMENT="production"

# Enable detailed logging
az webapp log config \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --application-logging filesystem \
  --detailed-error-messages true \
  --failed-request-tracing true \
  --web-server-logging filesystem
```

### 3. Deploy Using Git
```bash
# Configure local git deployment
az webapp deployment source config-local-git \
  --resource-group bultoo-rg \
  --name bultoo-api

# Get deployment credentials
az webapp deployment list-publishing-credentials \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --query "{username:publishingUserName, password:publishingPassword}"

# Add Azure remote (run from backend directory)
git remote add azure https://bultoo-api.scm.azurewebsites.net:443/bultoo-api.git

# Deploy
git add .
git commit -m "Initial Azure deployment"
git push azure main
```

### 4. Alternative: Deploy Using ZIP
```bash
# Create deployment package (run from backend directory)
zip -r deploy.zip . -x "*.git*" -x "*__pycache__*" -x "*.env*" -x "*venv*"

# Deploy
az webapp deployment source config-zip \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --src deploy.zip

# Clean up
rm deploy.zip
```

### 5. Verify Deployment
```bash
# Check deployment status
az webapp show \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --query state

# View logs
az webapp log tail \
  --resource-group bultoo-rg \
  --name bultoo-api

# Test endpoint
curl https://bultoo-api.azurewebsites.net/health
```

---

## Storage Setup

### 1. Create Storage Account
```bash
# Create storage account (globally unique name)
az storage account create \
  --name bultoostorage \
  --resource-group bultoo-rg \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2

# Get connection string
az storage account show-connection-string \
  --resource-group bultoo-rg \
  --name bultoostorage \
  --query connectionString -o tsv
```

### 2. Create Blob Containers
```bash
# Get storage key
STORAGE_KEY=$(az storage account keys list \
  --resource-group bultoo-rg \
  --account-name bultoostorage \
  --query '[0].value' -o tsv)

# Create container for media uploads
az storage container create \
  --name media \
  --account-name bultoostorage \
  --account-key $STORAGE_KEY \
  --public-access blob

# Create container for user avatars
az storage container create \
  --name avatars \
  --account-name bultoostorage \
  --account-key $STORAGE_KEY \
  --public-access blob

# Create container for private files
az storage container create \
  --name private \
  --account-name bultoostorage \
  --account-key $STORAGE_KEY \
  --public-access off
```

### 3. Configure CORS for Storage
```bash
# Enable CORS for storage account
az storage cors add \
  --services b \
  --methods GET POST PUT \
  --origins https://bultoo.com https://www.bultoo.com \
  --allowed-headers "*" \
  --exposed-headers "*" \
  --max-age 3600 \
  --account-name bultoostorage \
  --account-key $STORAGE_KEY
```

### 4. Add Storage Settings to Web App
```bash
# Get connection string
CONNECTION_STRING=$(az storage account show-connection-string \
  --resource-group bultoo-rg \
  --name bultoostorage \
  --query connectionString -o tsv)

# Update app settings
az webapp config appsettings set \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --settings \
    AZURE_STORAGE_CONNECTION_STRING="$CONNECTION_STRING" \
    AZURE_STORAGE_CONTAINER="media"
```

---

## CDN Configuration

### 1. Create CDN Profile
```bash
# Create CDN profile (Standard Microsoft tier)
az cdn profile create \
  --resource-group bultoo-rg \
  --name bultoo-cdn \
  --sku Standard_Microsoft

# Create CDN endpoint
az cdn endpoint create \
  --resource-group bultoo-rg \
  --name bultoo \
  --profile-name bultoo-cdn \
  --origin bultoostorage.blob.core.windows.net \
  --origin-host-header bultoostorage.blob.core.windows.net \
  --enable-compression true \
  --content-types-to-compress \
    "application/javascript" \
    "application/json" \
    "text/css" \
    "text/html" \
    "image/svg+xml"
```

### 2. Configure Custom Domain for CDN (Optional)
```bash
# Map custom domain (after DNS configuration)
az cdn custom-domain create \
  --resource-group bultoo-rg \
  --profile-name bultoo-cdn \
  --endpoint-name bultoo \
  --name cdn-bultoo \
  --hostname cdn.bultoo.com

# Enable HTTPS
az cdn custom-domain enable-https \
  --resource-group bultoo-rg \
  --profile-name bultoo-cdn \
  --endpoint-name bultoo \
  --name cdn-bultoo
```

### 3. Get CDN Endpoint URL
```bash
# Get endpoint hostname
az cdn endpoint show \
  --resource-group bultoo-rg \
  --name bultoo \
  --profile-name bultoo-cdn \
  --query hostName -o tsv
# Output: bultoo.azureedge.net
```

---

## Cost Estimation

### Free Tier Resources (with Azure Credits)
- **App Service**: F1 Free tier - $0/month (limited to 60 CPU minutes/day)
- **PostgreSQL**: Burstable B1ms - ~$12.41/month (can use credits)
- **Storage Account**: 5GB free, then ~$0.018/GB/month
- **CDN**: First 10GB free, then $0.081/GB

### Recommended Production Tier
- **App Service**: B1 Basic - ~$13.14/month
- **PostgreSQL**: Burstable B1ms - ~$12.41/month
- **Storage Account**: ~$1-5/month (for typical usage)
- **CDN**: ~$5-10/month (first 10GB free)

**Total Estimated Cost**: $30-40/month (excluding free tiers)

### Using Azure Credits Efficiently
```bash
# Monitor spending
az consumption usage list \
  --start-date 2025-01-01 \
  --end-date 2025-01-31

# Set up budget alerts
az consumption budget create \
  --budget-name bultoo-budget \
  --amount 50 \
  --category cost \
  --time-grain monthly \
  --start-date 2025-01-01 \
  --end-date 2025-12-31
```

---

## Monitoring and Scaling

### 1. Enable Application Insights
```bash
# Create Application Insights
az monitor app-insights component create \
  --app bultoo-insights \
  --location eastus \
  --resource-group bultoo-rg

# Get instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app bultoo-insights \
  --resource-group bultoo-rg \
  --query instrumentationKey -o tsv)

# Add to app settings
az webapp config appsettings set \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --settings \
    APPINSIGHTS_INSTRUMENTATIONKEY="$INSTRUMENTATION_KEY"
```

### 2. Configure Auto-scaling (Production)
```bash
# Create autoscale setting
az monitor autoscale create \
  --resource-group bultoo-rg \
  --resource bultoo-api \
  --resource-type Microsoft.Web/serverfarms \
  --name bultoo-autoscale \
  --min-count 1 \
  --max-count 3 \
  --count 1

# Add CPU-based scaling rule
az monitor autoscale rule create \
  --resource-group bultoo-rg \
  --autoscale-name bultoo-autoscale \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 1
```

### 3. Health Checks
```bash
# Configure health check endpoint
az webapp config set \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --health-check-path "/health"
```

---

## Useful Commands

### View Logs
```bash
# Stream application logs
az webapp log tail --resource-group bultoo-rg --name bultoo-api

# Download logs
az webapp log download --resource-group bultoo-rg --name bultoo-api --log-file logs.zip
```

### Restart Application
```bash
az webapp restart --resource-group bultoo-rg --name bultoo-api
```

### SSH into Container
```bash
az webapp ssh --resource-group bultoo-rg --name bultoo-api
```

### Update Environment Variables
```bash
az webapp config appsettings set \
  --resource-group bultoo-rg \
  --name bultoo-api \
  --settings KEY=VALUE
```

---

## Troubleshooting

### Common Issues

**1. Application not starting**
```bash
# Check logs
az webapp log tail --resource-group bultoo-rg --name bultoo-api

# Verify startup command
az webapp config show --resource-group bultoo-rg --name bultoo-api
```

**2. Database connection errors**
```bash
# Test connection from web app
az webapp ssh --resource-group bultoo-rg --name bultoo-api
# Inside container:
# python -c "import psycopg2; conn = psycopg2.connect('postgresql://...')"
```

**3. Slow performance**
```bash
# Scale up app service plan
az appservice plan update \
  --resource-group bultoo-rg \
  --name bultoo-plan \
  --sku B2
```

---

## Cleanup (for testing)

```bash
# Delete entire resource group (WARNING: deletes all resources)
az group delete --name bultoo-rg --yes --no-wait
```

---

## Next Steps
1. Configure custom domain (see DOMAIN_SETUP.md)
2. Set up CI/CD pipeline (see GitHub Actions section)
3. Generate APK for mobile testing (see APK_BUILD_GUIDE.md)

## Support Resources
- [Azure App Service Documentation](https://docs.microsoft.com/azure/app-service/)
- [Azure PostgreSQL Documentation](https://docs.microsoft.com/azure/postgresql/)
- [Azure Storage Documentation](https://docs.microsoft.com/azure/storage/)
