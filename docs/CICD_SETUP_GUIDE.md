# CI/CD Setup Guide for Boloo App

This comprehensive guide will walk you through setting up the complete CI/CD pipeline for the Boloo application using GitHub Actions.

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] GitHub repository with admin access
- [ ] Azure subscription with owner/contributor role
- [ ] Expo account (for mobile builds)
- [ ] Azure CLI installed locally
- [ ] GitHub CLI installed locally (optional but recommended)
- [ ] Node.js 18+ and Python 3.11+ installed

## 🚀 Quick Start (5 Minutes)

If you just want to get started quickly:

```bash
# 1. Clone the repository
git clone https://github.com/your-org/boloo-app.git
cd boloo-app

# 2. Run the verification workflow
gh workflow run verify-setup.yml

# 3. Check the results
gh run list --workflow=verify-setup.yml
```

This will identify what's missing and needs to be configured.

## 📝 Detailed Setup Instructions

### Step 1: Azure Infrastructure Setup

#### 1.1 Create Azure Resources

```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "Your Subscription Name"

# Create resource group
az group create --name boloo-resources --location eastus

# Create production backend App Service
az appservice plan create \
  --name boloo-plan \
  --resource-group boloo-resources \
  --sku B1 \
  --is-linux

az webapp create \
  --name boloo-backend-prod \
  --resource-group boloo-resources \
  --plan boloo-plan \
  --runtime "PYTHON:3.11"

# Create staging backend App Service
az webapp create \
  --name boloo-backend-staging \
  --resource-group boloo-resources \
  --plan boloo-plan \
  --runtime "PYTHON:3.11"

# Create staging deployment slot
az webapp deployment slot create \
  --name boloo-backend-prod \
  --resource-group boloo-resources \
  --slot staging

# Create PostgreSQL database
az postgres flexible-server create \
  --name boloo-db \
  --resource-group boloo-resources \
  --location eastus \
  --admin-user booloadmin \
  --admin-password 'YourSecurePassword123!' \
  --sku-name Standard_B1ms \
  --version 15

# Create production database
az postgres flexible-server db create \
  --server-name boloo-db \
  --resource-group boloo-resources \
  --database-name boloo_prod

# Create staging database
az postgres flexible-server db create \
  --server-name boloo-db \
  --resource-group boloo-resources \
  --database-name boloo_staging

# Create Static Web App for frontend
az staticwebapp create \
  --name boloo-web \
  --resource-group boloo-resources \
  --location eastus2
```

#### 1.2 Get Azure Credentials for GitHub Actions

```bash
# Create service principal
az ad sp create-for-rbac \
  --name "boloo-github-actions" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/boloo-resources \
  --sdk-auth

# Copy the JSON output - you'll need this for AZURE_CREDENTIALS secret
```

#### 1.3 Get Static Web Apps Token

```bash
# Get deployment token for production
az staticwebapp secrets list \
  --name boloo-web \
  --resource-group boloo-resources \
  --query "properties.apiKey" \
  --output tsv

# Copy this token for AZURE_STATIC_WEB_APPS_API_TOKEN
```

### Step 2: Expo Configuration

#### 2.1 Install EAS CLI

```bash
npm install -g eas-cli
```

#### 2.2 Login to Expo

```bash
eas login
```

#### 2.3 Configure EAS Build

```bash
cd mobile
eas build:configure
```

#### 2.4 Create Expo Access Token

1. Go to https://expo.dev/accounts/[account]/settings/access-tokens
2. Click "Create Token"
3. Give it a name: "GitHub Actions"
4. Copy the token (you'll need this for EXPO_TOKEN secret)

### Step 3: GitHub Secrets Configuration

#### 3.1 Using GitHub Web Interface

1. Go to your repository on GitHub
2. Navigate to: **Settings → Secrets and variables → Actions**
3. Click **New repository secret**
4. Add each secret listed below

#### 3.2 Using GitHub CLI (Faster)

```bash
# Set Azure credentials (multi-line JSON)
gh secret set AZURE_CREDENTIALS < azure-credentials.json

# Set single-line secrets
gh secret set AZURE_RESOURCE_GROUP -b "boloo-resources"
gh secret set DATABASE_URL -b "postgresql://booloadmin:YourPassword@boloo-db.postgres.database.azure.com/boloo_prod"
gh secret set SECRET_KEY -b "$(openssl rand -hex 32)"
gh secret set STAGING_DATABASE_URL -b "postgresql://booloadmin:YourPassword@boloo-db.postgres.database.azure.com/boloo_staging"
gh secret set STAGING_SECRET_KEY -b "$(openssl rand -hex 32)"
gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN -b "your-static-web-apps-token"
gh secret set NEXT_PUBLIC_API_URL -b "https://boloo-backend-prod.azurewebsites.net"
gh secret set STAGING_API_URL -b "https://boloo-backend-staging.azurewebsites.net"
gh secret set EXPO_TOKEN -b "your-expo-token"
gh secret set EXPO_PUBLIC_API_URL -b "https://api.boloo.app"

# Optional: Notification secrets
gh secret set SLACK_WEBHOOK_URL -b "https://hooks.slack.com/services/YOUR/WEBHOOK"

# Optional: Code quality secrets
gh secret set SONAR_TOKEN -b "your-sonarcloud-token"
gh secret set SNYK_TOKEN -b "your-snyk-token"
```

### Step 4: Environment Configuration

#### 4.1 Create Production Environment

1. Go to **Settings → Environments**
2. Click **New environment**
3. Name: `production`
4. Add protection rules:
   - ✅ Required reviewers (1-2 people)
   - ✅ Wait timer (optional: 5 minutes)
5. Add environment secrets/variables:
   - `AZURE_WEBAPP_NAME`: boloo-backend-prod
   - `WEB_APP_URL`: https://boloo.app

#### 4.2 Create Staging Environment

1. Create another environment: `staging`
2. No protection rules needed for staging
3. Add environment variables:
   - `AZURE_WEBAPP_NAME`: boloo-backend-staging
   - `WEB_APP_URL`: https://staging.boloo.app

### Step 5: Branch Protection Rules

#### 5.1 Protect Main Branch

1. Go to **Settings → Branches**
2. Click **Add rule**
3. Branch name pattern: `main`
4. Enable:
   - ✅ Require a pull request before merging
   - ✅ Require approvals (1)
   - ✅ Require status checks to pass
   - ✅ Require branches to be up to date
5. Add required status checks:
   - `Backend Tests`
   - `Web Tests`
   - `Mobile Tests`
   - `Security Scan`

### Step 6: Test Your Setup

#### 6.1 Verify Setup Workflow

```bash
# Run verification workflow
gh workflow run verify-setup.yml

# Wait a moment, then check results
gh run list --workflow=verify-setup.yml

# View detailed logs
gh run view --log
```

#### 6.2 Test Individual Workflows

```bash
# Test backend deployment to staging
gh workflow run deploy-backend.yml -f environment=staging

# Test web deployment (create a test branch)
git checkout -b test/web-deploy
git push origin test/web-deploy
# Create PR to trigger web deployment

# Test mobile build
gh workflow run build-mobile.yml -f platform=android -f profile=preview
```

#### 6.3 Create Test Pull Request

```bash
# Create a feature branch
git checkout -b feature/test-ci
echo "# Test" >> README.md
git add README.md
git commit -m "test: verify CI pipeline"
git push origin feature/test-ci

# Create PR
gh pr create --title "Test CI Pipeline" --body "Testing automated CI/CD workflows"

# Watch the checks run
gh pr checks
```

### Step 7: Configure Notifications (Optional)

#### 7.1 Slack Integration

1. Create a Slack webhook:
   - Go to https://api.slack.com/messaging/webhooks
   - Create a new webhook for your workspace
   - Copy the webhook URL

2. Add to GitHub secrets:
   ```bash
   gh secret set SLACK_WEBHOOK_URL -b "https://hooks.slack.com/services/YOUR/WEBHOOK"
   ```

#### 7.2 Email Notifications

GitHub sends email notifications by default. Configure in:
**Settings → Notifications → Actions**

### Step 8: Database Migrations Setup

#### 8.1 Configure Alembic

```bash
# In backend directory
cd backend

# Initialize Alembic (if not already done)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Test migration locally
alembic upgrade head
```

#### 8.2 Azure Database Configuration

```bash
# Allow GitHub Actions IP ranges (or use service endpoint)
az postgres flexible-server firewall-rule create \
  --resource-group boloo-resources \
  --name boloo-db \
  --rule-name AllowGitHubActions \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 255.255.255.255

# Note: Use more restrictive IP ranges in production
```

## 🔍 Verification Checklist

After setup, verify each component:

### Azure Resources
- [ ] App Services created and running
- [ ] PostgreSQL databases accessible
- [ ] Static Web App configured
- [ ] Service principal has correct permissions

### GitHub Configuration
- [ ] All required secrets added
- [ ] Environments created (production, staging)
- [ ] Branch protection rules enabled
- [ ] Workflows visible in Actions tab

### Application Configuration
- [ ] Backend connects to database
- [ ] Web app builds successfully
- [ ] Mobile app configuration valid
- [ ] Environment variables set correctly

### CI/CD Pipeline
- [ ] Test workflow runs on PRs
- [ ] Backend deployment workflow exists
- [ ] Web deployment workflow exists
- [ ] Mobile build workflow exists
- [ ] Staging deployment workflow exists

## 🚨 Troubleshooting

### Common Issues and Solutions

#### 1. "Authentication failed" during Azure deployment

**Problem**: Service principal doesn't have correct permissions

**Solution**:
```bash
# Recreate service principal with correct scope
az ad sp create-for-rbac \
  --name "boloo-github-actions" \
  --role contributor \
  --scopes /subscriptions/{subscription-id} \
  --sdk-auth
```

#### 2. Database connection fails

**Problem**: Firewall rules blocking GitHub Actions

**Solution**:
```bash
# Add firewall rule for Azure services
az postgres flexible-server firewall-rule create \
  --resource-group boloo-resources \
  --name boloo-db \
  --rule-name AllowAllAzureIPs \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

#### 3. Expo build fails

**Problem**: Invalid or expired Expo token

**Solution**:
```bash
# Generate new token
eas login
# Go to https://expo.dev/accounts/[account]/settings/access-tokens
# Create new token and update GitHub secret
gh secret set EXPO_TOKEN -b "new-token"
```

#### 4. Static Web App deployment fails

**Problem**: Invalid deployment token

**Solution**:
```bash
# Get new token
az staticwebapp secrets list \
  --name boloo-web \
  --resource-group boloo-resources \
  --query "properties.apiKey"

# Update secret
gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN -b "new-token"
```

## 📊 Monitoring Your CI/CD

### View Workflow Runs

```bash
# List recent runs
gh run list

# View specific run
gh run view [run-id]

# Download logs
gh run download [run-id]
```

### Monitor Azure Resources

```bash
# View App Service logs
az webapp log tail --name boloo-backend-prod --resource-group boloo-resources

# Check database metrics
az postgres flexible-server show \
  --name boloo-db \
  --resource-group boloo-resources
```

## 🔐 Security Best Practices

1. **Rotate Secrets Regularly**
   - Service principal credentials: Every 90 days
   - Database passwords: Every 180 days
   - API tokens: When team members leave

2. **Use Least Privilege**
   - Service principals: Only necessary permissions
   - Database users: Read-only for non-production

3. **Enable Security Features**
   - GitHub secret scanning
   - Dependabot alerts
   - CodeQL analysis

4. **Audit Access**
   - Review who has repository admin access
   - Monitor workflow execution logs
   - Check Azure resource access regularly

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Azure App Service CI/CD](https://docs.microsoft.com/en-us/azure/app-service/deploy-github-actions)
- [Expo EAS Build](https://docs.expo.dev/build/introduction/)
- [Azure Static Web Apps](https://docs.microsoft.com/en-us/azure/static-web-apps/)

## 🎯 Next Steps

After completing this setup:

1. ✅ Create your first production deployment
2. ✅ Set up monitoring and alerting
3. ✅ Configure automated backups
4. ✅ Document your deployment process
5. ✅ Train your team on the CI/CD workflows

## 💡 Tips for Success

- **Start with staging**: Always test in staging before production
- **Small iterations**: Deploy small changes frequently
- **Monitor metrics**: Watch build times, test coverage, deployment frequency
- **Keep workflows DRY**: Use composite actions for repeated logic
- **Document changes**: Update this guide as you customize workflows

---

**Questions or Issues?**

- Check the [Troubleshooting](#troubleshooting) section
- Review workflow logs: `gh run view --log`
- Open an issue in the repository
- Contact the DevOps team

**Last Updated**: 2025-11-22
**Version**: 1.0.0
