# Environment Setup Guide

## Overview

This guide provides comprehensive instructions for configuring development, staging, and production environments for the Boloo application, including environment variables, secrets management, and best practices.

## Table of Contents

1. [Environment Overview](#environment-overview)
2. [Development Environment](#development-environment)
3. [Staging Environment](#staging-environment)
4. [Production Environment](#production-environment)
5. [Environment Variables](#environment-variables)
6. [Secrets Management](#secrets-management)
7. [Azure Key Vault Integration](#azure-key-vault-integration)
8. [Database Configuration](#database-configuration)
9. [Third-Party Services](#third-party-services)
10. [Environment Switching](#environment-switching)

---

## Environment Overview

### Environment Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    Environment Hierarchy                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Development (Local)                                        │
│  ├── Purpose: Local development and testing                │
│  ├── Data: Synthetic/mock data                             │
│  ├── Services: Docker Compose                              │
│  └── Deployment: Manual (npm run dev)                      │
│                                                              │
│  Staging (Azure)                                            │
│  ├── Purpose: QA testing and client demos                  │
│  ├── Data: Production-like data (anonymized)               │
│  ├── Services: Azure (scaled down)                         │
│  └── Deployment: Automated (CI/CD)                         │
│                                                              │
│  Production (Azure)                                         │
│  ├── Purpose: Live application serving users               │
│  ├── Data: Real user data                                  │
│  ├── Services: Azure (full scale)                          │
│  └── Deployment: Manual approval (CI/CD)                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Environment Comparison

| Feature | Development | Staging | Production |
|---------|------------|---------|------------|
| **Infrastructure** | Local/Docker | Azure (B-tier) | Azure (P-tier) |
| **Database** | PostgreSQL (local) | PostgreSQL Flexible | PostgreSQL Flexible |
| **Cache** | Redis (local) | Azure Redis Basic | Azure Redis Standard |
| **Storage** | Local filesystem | Azure Blob (test) | Azure Blob (prod) |
| **Monitoring** | Console logs | App Insights (limited) | App Insights (full) |
| **SSL** | Self-signed | Azure managed | Azure managed |
| **Auto-scaling** | No | Limited | Yes |
| **Deployment** | Manual | Automated | Manual approval |

---

## Development Environment

### Local Machine Setup

#### Prerequisites

```bash
# Install Node.js 18 LTS
nvm install 18
nvm use 18

# Install PostgreSQL 14+
brew install postgresql@14  # macOS
# or
sudo apt-get install postgresql-14  # Ubuntu

# Install Redis
brew install redis  # macOS
# or
sudo apt-get install redis-server  # Ubuntu

# Install Azure CLI (for Key Vault access)
brew install azure-cli  # macOS
# or
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash  # Ubuntu
```

#### Project Setup

```bash
# Clone repository
git clone https://github.com/your-org/boloo-app.git
cd boloo-app

# Install dependencies
npm install

# Setup Git hooks (optional)
npm run prepare
```

#### Docker Compose Setup (Alternative)

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    container_name: boloo-postgres-dev
    environment:
      POSTGRES_DB: boloo_dev
      POSTGRES_USER: boloo_dev
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d

  redis:
    image: redis:7-alpine
    container_name: boloo-redis-dev
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  mailhog:
    image: mailhog/mailhog
    container_name: boloo-mailhog-dev
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI

volumes:
  postgres_data:
  redis_data:
```

```bash
# Start development services
docker-compose -f docker-compose.dev.yml up -d

# Stop services
docker-compose -f docker-compose.dev.yml down
```

#### Environment Configuration

```bash
# Create .env.development file
cp .env.example .env.development
```

```env
# .env.development
NODE_ENV=development
PORT=3000

# Database
DATABASE_URL=postgresql://boloo_dev:dev_password@localhost:5432/boloo_dev
DATABASE_SSL=false

# Redis
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=

# Authentication
JWT_SECRET=dev-jwt-secret-change-in-production
JWT_EXPIRATION=1h
REFRESH_TOKEN_EXPIRATION=7d

# Email (MailHog for testing)
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_SECURE=false
SMTP_FROM=noreply@boloo.local

# Stripe (Test Mode)
STRIPE_API_KEY=sk_test_your_test_key_here
STRIPE_WEBHOOK_SECRET=whsec_test_your_webhook_secret

# Storage (Local)
AZURE_STORAGE_ACCOUNT=devstoreaccount1
AZURE_STORAGE_KEY=
STORAGE_CONTAINER=dev-uploads

# Logging
LOG_LEVEL=debug
LOG_FORMAT=pretty

# Feature Flags
FEATURE_PAYMENTS_ENABLED=true
FEATURE_SMS_ENABLED=false
```

#### Database Setup

```bash
# Create database
createdb boloo_dev

# Run migrations
npm run db:migrate:dev

# Seed database with test data
npm run db:seed:dev

# Verify setup
npm run db:status
```

#### Running Development Server

```bash
# Start development server with hot reload
npm run dev

# Run with debugging
npm run dev:debug

# Run tests in watch mode
npm run test:watch
```

---

## Staging Environment

### Azure Resources (Staging)

```yaml
Resource Group: boloo-staging-rg
Location: East US

Resources:
  App Service:
    Name: boloo-backend-staging
    Plan: B1 (Basic)
    Instances: 1

  PostgreSQL:
    Name: boloo-postgres-staging
    Tier: Burstable B1ms
    Storage: 32 GB

  Redis:
    Name: boloo-redis-staging
    Tier: Basic C0 (250 MB)

  Storage Account:
    Name: boloostagestg
    Tier: Standard LRS

  Key Vault:
    Name: boloo-kv-staging
```

### Environment Configuration

```bash
# Azure App Service Configuration
az webapp config appsettings set \
  --name boloo-backend-staging \
  --resource-group boloo-staging-rg \
  --settings \
    NODE_ENV=staging \
    PORT=8080
```

```env
# Staging Environment Variables (stored in Azure App Service)
NODE_ENV=staging
PORT=8080

# Database (from Key Vault)
DATABASE_URL=@Microsoft.KeyVault(SecretUri=https://boloo-kv-staging.vault.azure.net/secrets/database-url/)
DATABASE_SSL=true
DATABASE_POOL_MIN=2
DATABASE_POOL_MAX=10

# Redis (from Key Vault)
REDIS_URL=@Microsoft.KeyVault(SecretUri=https://boloo-kv-staging.vault.azure.net/secrets/redis-url/)

# Authentication
JWT_SECRET=@Microsoft.KeyVault(SecretUri=https://boloo-kv-staging.vault.azure.net/secrets/jwt-secret/)
JWT_EXPIRATION=1h

# Email (SendGrid Test)
SENDGRID_API_KEY=@Microsoft.KeyVault(SecretUri=https://boloo-kv-staging.vault.azure.net/secrets/sendgrid-api-key/)
SENDGRID_FROM_EMAIL=staging@boloo.com

# Stripe (Test Mode)
STRIPE_API_KEY=@Microsoft.KeyVault(SecretUri=https://boloo-kv-staging.vault.azure.net/secrets/stripe-test-key/)
STRIPE_WEBHOOK_SECRET=@Microsoft.KeyVault(SecretUri=https://boloo-kv-staging.vault.azure.net/secrets/stripe-webhook-test/)

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=@Microsoft.KeyVault(SecretUri=https://boloo-kv-staging.vault.azure.net/secrets/storage-connection-string/)
STORAGE_CONTAINER=staging-uploads

# Application Insights
APPINSIGHTS_INSTRUMENTATIONKEY=@Microsoft.KeyVault(SecretUri=https://boloo-kv-staging.vault.azure.net/secrets/appinsights-key/)

# Logging
LOG_LEVEL=info
LOG_FORMAT=json

# Feature Flags
FEATURE_PAYMENTS_ENABLED=true
FEATURE_SMS_ENABLED=true

# API Base URL
API_BASE_URL=https://boloo-backend-staging.azurewebsites.net
```

### Deployment Slot Configuration

```bash
# Create staging slot
az webapp deployment slot create \
  --name boloo-backend-staging \
  --resource-group boloo-staging-rg \
  --slot preview

# Configure slot-specific settings
az webapp config appsettings set \
  --name boloo-backend-staging \
  --resource-group boloo-staging-rg \
  --slot preview \
  --slot-settings SLOT_NAME=preview
```

---

## Production Environment

### Azure Resources (Production)

```yaml
Resource Group: boloo-prod-rg
Location: East US

Resources:
  App Service:
    Name: boloo-backend-api
    Plan: P1V2 (Premium)
    Instances: 2-10 (auto-scale)

  PostgreSQL:
    Name: boloo-postgres-prod
    Tier: General Purpose D2s_v3
    Storage: 128 GB
    High Availability: Zone Redundant

  Redis:
    Name: boloo-redis-prod
    Tier: Standard C1 (1 GB)
    Replication: Enabled

  Storage Account:
    Name: boloostorage
    Tier: Standard GRS

  Key Vault:
    Name: boloo-keyvault
    SKU: Standard
    Soft Delete: Enabled
    Purge Protection: Enabled
```

### Environment Configuration

```bash
# Production App Service Configuration
az webapp config appsettings set \
  --name boloo-backend-api \
  --resource-group boloo-prod-rg \
  --settings \
    NODE_ENV=production \
    PORT=8080 \
    WEBSITE_NODE_DEFAULT_VERSION=18-lts
```

```env
# Production Environment Variables (Azure App Service)
NODE_ENV=production
PORT=8080
WEBSITE_NODE_DEFAULT_VERSION=18-lts

# Database (from Key Vault)
DATABASE_URL=@Microsoft.KeyVault(SecretUri=https://boloo-keyvault.vault.azure.net/secrets/database-url/)
DATABASE_SSL=true
DATABASE_POOL_MIN=5
DATABASE_POOL_MAX=20
DATABASE_STATEMENT_TIMEOUT=30000

# Redis (from Key Vault)
REDIS_URL=@Microsoft.KeyVault(SecretUri=https://boloo-keyvault.vault.azure.net/secrets/redis-url/)
REDIS_PASSWORD=@Microsoft.KeyVault(SecretUri=https://boloo-keyvault.vault.azure.net/secrets/redis-password/)
REDIS_TLS=true

# Authentication
JWT_SECRET=@Microsoft.KeyVault(SecretUri=https://boloo-keyvault.vault.azure.net/secrets/jwt-secret/)
JWT_EXPIRATION=15m
REFRESH_TOKEN_EXPIRATION=7d
JWT_ISSUER=https://api.bultoo.com

# Email (SendGrid Production)
SENDGRID_API_KEY=@Microsoft.KeyVault(SecretUri=https://boloo-keyvault.vault.azure.net/secrets/sendgrid-api-key/)
SENDGRID_FROM_EMAIL=noreply@bultoo.com
SENDGRID_FROM_NAME=Boloo

# Stripe (Live Mode)
STRIPE_API_KEY=@Microsoft.KeyVault(SecretUri=https://boloo-keyvault.vault.azure.net/secrets/stripe-live-key/)
STRIPE_WEBHOOK_SECRET=@Microsoft.KeyVault(SecretUri=https://boloo-keyvault.vault.azure.net/secrets/stripe-webhook-live/)
STRIPE_PUBLISHABLE_KEY=@Microsoft.KeyVault(SecretUri=https://boloo-keyvault.vault.azure.net/secrets/stripe-publishable-key/)

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=@Microsoft.KeyVault(SecretUri=https://boloo-keyvault.vault.azure.net/secrets/storage-connection-string/)
STORAGE_CONTAINER=uploads
STORAGE_CDN_URL=https://cdn.bultoo.com

# Application Insights
APPINSIGHTS_INSTRUMENTATIONKEY=@Microsoft.KeyVault(SecretUri=https://boloo-keyvault.vault.azure.net/secrets/appinsights-key/)
APPINSIGHTS_SAMPLING_PERCENTAGE=10

# Security
CORS_ORIGIN=https://admin.bultoo.com,https://www.bultoo.com
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQUESTS=100
HELMET_ENABLED=true

# Logging
LOG_LEVEL=warn
LOG_FORMAT=json

# Feature Flags
FEATURE_PAYMENTS_ENABLED=true
FEATURE_SMS_ENABLED=true
FEATURE_ANALYTICS_ENABLED=true

# API Configuration
API_BASE_URL=https://api.bultoo.com
ADMIN_URL=https://admin.bultoo.com

# Performance
CLUSTER_MODE=true
COMPRESSION_ENABLED=true
CACHE_TTL=300
```

---

## Environment Variables

### Variable Naming Convention

```
Format: UPPERCASE_SNAKE_CASE

Categories:
- NODE_ENV               → Runtime environment
- DATABASE_*            → Database configuration
- REDIS_*               → Redis configuration
- JWT_*                 → Authentication
- STRIPE_*              → Payment gateway
- SENDGRID_*            → Email service
- AZURE_*               → Azure services
- FEATURE_*             → Feature flags
- LOG_*                 → Logging configuration
```

### Required Variables by Environment

#### Development

```env
# Minimal required variables
NODE_ENV=development
DATABASE_URL=postgresql://user:pass@localhost:5432/db
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-dev-secret
STRIPE_API_KEY=sk_test_***
```

#### Staging

```env
# All development variables plus:
APPINSIGHTS_INSTRUMENTATIONKEY=***
AZURE_STORAGE_CONNECTION_STRING=***
SENDGRID_API_KEY=***
```

#### Production

```env
# All staging variables plus:
CORS_ORIGIN=https://admin.bultoo.com
RATE_LIMIT_MAX_REQUESTS=100
HELMET_ENABLED=true
CLUSTER_MODE=true
# All secrets from Key Vault
```

### Environment Variable Validation

```javascript
// config/env-validation.js
const Joi = require('joi');

const envSchema = Joi.object({
  NODE_ENV: Joi.string()
    .valid('development', 'staging', 'production')
    .required(),

  PORT: Joi.number()
    .default(3000),

  DATABASE_URL: Joi.string()
    .uri()
    .required(),

  REDIS_URL: Joi.string()
    .uri()
    .required(),

  JWT_SECRET: Joi.string()
    .min(32)
    .required(),

  STRIPE_API_KEY: Joi.string()
    .pattern(/^sk_(test|live)_/)
    .required(),

  // Add more validations...
}).unknown();

const { error, value: validatedEnv } = envSchema.validate(process.env);

if (error) {
  throw new Error(`Environment validation error: ${error.message}`);
}

module.exports = validatedEnv;
```

---

## Secrets Management

### Azure Key Vault Integration

#### Setup Key Vault

```bash
# Create Key Vault
az keyvault create \
  --name boloo-keyvault \
  --resource-group boloo-prod-rg \
  --location eastus \
  --enable-soft-delete true \
  --enable-purge-protection true

# Grant App Service access
az webapp identity assign \
  --name boloo-backend-api \
  --resource-group boloo-prod-rg

# Get managed identity principal ID
PRINCIPAL_ID=$(az webapp identity show \
  --name boloo-backend-api \
  --resource-group boloo-prod-rg \
  --query principalId \
  --output tsv)

# Set Key Vault access policy
az keyvault set-policy \
  --name boloo-keyvault \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get list
```

#### Store Secrets

```bash
# Database connection string
az keyvault secret set \
  --vault-name boloo-keyvault \
  --name database-url \
  --value "postgresql://user:pass@server.postgres.database.azure.com:5432/boloo_prod?ssl=true"

# Redis connection string
az keyvault secret set \
  --vault-name boloo-keyvault \
  --name redis-url \
  --value "rediss://boloo-redis-prod.redis.cache.windows.net:6380"

# JWT secret
az keyvault secret set \
  --vault-name boloo-keyvault \
  --name jwt-secret \
  --value "$(openssl rand -base64 32)"

# Stripe API key
az keyvault secret set \
  --vault-name boloo-keyvault \
  --name stripe-live-key \
  --value "sk_live_your_stripe_key"

# SendGrid API key
az keyvault secret set \
  --vault-name boloo-keyvault \
  --name sendgrid-api-key \
  --value "SG.your_sendgrid_key"

# Storage connection string
az keyvault secret set \
  --vault-name boloo-keyvault \
  --name storage-connection-string \
  --value "DefaultEndpointsProtocol=https;AccountName=boloostorage;..."
```

#### Reference Secrets in App Service

```bash
# Configure App Service to use Key Vault references
az webapp config appsettings set \
  --name boloo-backend-api \
  --resource-group boloo-prod-rg \
  --settings \
    DATABASE_URL="@Microsoft.KeyVault(SecretUri=https://boloo-keyvault.vault.azure.net/secrets/database-url/)" \
    REDIS_URL="@Microsoft.KeyVault(SecretUri=https://boloo-keyvault.vault.azure.net/secrets/redis-url/)" \
    JWT_SECRET="@Microsoft.KeyVault(SecretUri=https://boloo-keyvault.vault.azure.net/secrets/jwt-secret/)" \
    STRIPE_API_KEY="@Microsoft.KeyVault(SecretUri=https://boloo-keyvault.vault.azure.net/secrets/stripe-live-key/)" \
    SENDGRID_API_KEY="@Microsoft.KeyVault(SecretUri=https://boloo-keyvault.vault.azure.net/secrets/sendgrid-api-key/)"
```

### Secret Rotation

```bash
# Rotate JWT secret
NEW_JWT_SECRET=$(openssl rand -base64 32)

az keyvault secret set \
  --vault-name boloo-keyvault \
  --name jwt-secret \
  --value "$NEW_JWT_SECRET"

# Restart app to pick up new secret
az webapp restart \
  --name boloo-backend-api \
  --resource-group boloo-prod-rg
```

### Local Development with Key Vault

```bash
# Login to Azure
az login

# Set Key Vault name
export KEY_VAULT_NAME=boloo-kv-staging

# Fetch secrets for local development
az keyvault secret show \
  --vault-name $KEY_VAULT_NAME \
  --name database-url \
  --query value \
  --output tsv > .env.local
```

---

## Database Configuration

### Connection String Format

```
# PostgreSQL connection string
postgresql://[user]:[password]@[host]:[port]/[database]?ssl=true&sslmode=require

# Example
postgresql://boloo_admin:SecurePass123@boloo-postgres-prod.postgres.database.azure.com:5432/boloo_prod?ssl=true&sslmode=require
```

### Connection Pooling

```javascript
// config/database.js
const { Pool } = require('pg');

const poolConfig = {
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.DATABASE_SSL === 'true' ? {
    rejectUnauthorized: true
  } : false,

  // Pool configuration
  min: parseInt(process.env.DATABASE_POOL_MIN || '2'),
  max: parseInt(process.env.DATABASE_POOL_MAX || '10'),

  // Timeouts
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,

  // Error handling
  allowExitOnIdle: false
};

const pool = new Pool(poolConfig);

// Error handling
pool.on('error', (err, client) => {
  console.error('Unexpected database error:', err);
});

module.exports = pool;
```

### Environment-Specific Database URLs

```bash
# Development
DATABASE_URL=postgresql://boloo_dev:dev_password@localhost:5432/boloo_dev

# Staging
DATABASE_URL=postgresql://boloo_admin:***@boloo-postgres-staging.postgres.database.azure.com:5432/boloo_staging?ssl=true

# Production
DATABASE_URL=postgresql://boloo_admin:***@boloo-postgres-prod.postgres.database.azure.com:5432/boloo_prod?ssl=true&sslmode=require
```

---

## Third-Party Services

### Stripe Configuration

```env
# Development (Test Mode)
STRIPE_API_KEY=sk_test_51...
STRIPE_WEBHOOK_SECRET=whsec_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_51...

# Production (Live Mode)
STRIPE_API_KEY=sk_live_51...
STRIPE_WEBHOOK_SECRET=whsec_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_51...
```

### SendGrid Configuration

```env
# All environments use same API key but different templates
SENDGRID_API_KEY=SG.xxx
SENDGRID_FROM_EMAIL=noreply@bultoo.com
SENDGRID_FROM_NAME=Boloo

# Template IDs (different per environment)
SENDGRID_TEMPLATE_WELCOME=d-xxx  # Staging: d-yyy
SENDGRID_TEMPLATE_ORDER_CONFIRMATION=d-zzz
```

### Azure Storage Configuration

```env
# Development (Azure Storage Emulator)
AZURE_STORAGE_CONNECTION_STRING=UseDevelopmentStorage=true

# Staging
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=boloostagestg;...
STORAGE_CONTAINER=staging-uploads

# Production
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=boloostorage;...
STORAGE_CONTAINER=uploads
STORAGE_CDN_URL=https://cdn.bultoo.com
```

---

## Environment Switching

### Using .env Files

```bash
# .env.development
NODE_ENV=development
# ... development variables

# .env.staging
NODE_ENV=staging
# ... staging variables

# .env.production
NODE_ENV=production
# ... production variables
```

### dotenv-cli Usage

```bash
# Install
npm install --save-dev dotenv-cli

# Run with specific environment
npx dotenv -e .env.development npm run dev
npx dotenv -e .env.staging npm run start
npx dotenv -e .env.production npm run start
```

### package.json Scripts

```json
{
  "scripts": {
    "dev": "dotenv -e .env.development nodemon src/server.js",
    "start:staging": "dotenv -e .env.staging node src/server.js",
    "start:prod": "dotenv -e .env.production node src/server.js",

    "db:migrate:dev": "dotenv -e .env.development npx sequelize-cli db:migrate",
    "db:migrate:staging": "dotenv -e .env.staging npx sequelize-cli db:migrate",
    "db:migrate:prod": "dotenv -e .env.production npx sequelize-cli db:migrate"
  }
}
```

### Environment Detection

```javascript
// config/index.js
const env = process.env.NODE_ENV || 'development';

const configs = {
  development: require('./development'),
  staging: require('./staging'),
  production: require('./production')
};

module.exports = configs[env];
```

---

## Best Practices

### Security

1. **Never commit secrets** to version control
2. **Use Key Vault** for production secrets
3. **Rotate secrets** regularly (quarterly minimum)
4. **Limit access** to production environments
5. **Audit secret access** regularly

### Configuration

1. **Validate environment variables** on startup
2. **Use defaults** for non-critical settings
3. **Document required variables** in README
4. **Use type-safe configuration** (TypeScript)

### Deployment

1. **Test configurations** in staging first
2. **Use deployment slots** for zero-downtime
3. **Verify secrets** after deployment
4. **Monitor applications** after config changes

---

## Troubleshooting

### Common Issues

#### Key Vault Access Denied

```bash
# Verify managed identity is enabled
az webapp identity show \
  --name boloo-backend-api \
  --resource-group boloo-prod-rg

# Verify Key Vault access policy
az keyvault show \
  --name boloo-keyvault \
  --query properties.accessPolicies
```

#### Database Connection Failed

```bash
# Test database connectivity
psql "$DATABASE_URL"

# Check firewall rules
az postgres flexible-server firewall-rule list \
  --resource-group boloo-prod-rg \
  --server-name boloo-postgres-prod
```

#### Environment Variable Not Loading

```bash
# Verify App Service settings
az webapp config appsettings list \
  --name boloo-backend-api \
  --resource-group boloo-prod-rg

# Check application logs
az webapp log tail \
  --name boloo-backend-api \
  --resource-group boloo-prod-rg
```

---

## Next Steps

1. Review [Domain Configuration](./DOMAIN_CONFIGURATION_GUIDE.md) for custom domain setup
2. Check [Cloud Architecture](./CLOUD_ARCHITECTURE.md) for infrastructure overview
3. Follow [Production Checklist](./PRODUCTION_DEPLOYMENT_CHECKLIST.md) before deployment
4. Review [Development Roadmap](./DEVELOPMENT_ROADMAP.md) for feature planning

