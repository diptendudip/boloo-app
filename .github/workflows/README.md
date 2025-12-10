# GitHub Actions CI/CD Workflows

This directory contains comprehensive GitHub Actions workflows for automated testing, building, and deployment of the Boloo application.

## 📋 Table of Contents

- [Workflows Overview](#workflows-overview)
- [Setup Requirements](#setup-requirements)
- [GitHub Secrets Configuration](#github-secrets-configuration)
- [Workflow Details](#workflow-details)
- [Status Badges](#status-badges)
- [Troubleshooting](#troubleshooting)

## 🔄 Workflows Overview

| Workflow | Trigger | Purpose | Status |
|----------|---------|---------|--------|
| **test.yml** | Pull Requests | Run comprehensive tests for all components | ![CI Tests](https://github.com/your-org/boloo-app/workflows/Continuous%20Integration%20Tests/badge.svg) |
| **deploy-backend.yml** | Push to main (backend/**) | Deploy backend to Azure App Service | ![Backend Deploy](https://github.com/your-org/boloo-app/workflows/Deploy%20Backend%20to%20Azure/badge.svg) |
| **deploy-web.yml** | Push to main (web/**) | Deploy web app to Azure Static Web Apps | ![Web Deploy](https://github.com/your-org/boloo-app/workflows/Deploy%20Web%20to%20Azure%20Static%20Web%20Apps/badge.svg) |
| **build-mobile.yml** | Push to main (mobile/**) | Build mobile app with EAS Build | ![Mobile Build](https://github.com/your-org/boloo-app/workflows/Build%20Mobile%20App/badge.svg) |
| **deploy-staging.yml** | Push to develop | Deploy to staging environment | ![Staging Deploy](https://github.com/your-org/boloo-app/workflows/Deploy%20to%20Staging%20Environment/badge.svg) |
| **dependency-update.yml** | Weekly schedule | Update dependencies and security audit | ![Dependency Updates](https://github.com/your-org/boloo-app/workflows/Dependency%20Updates%20&%20Security/badge.svg) |

## 🔧 Setup Requirements

### Prerequisites

1. **Azure Account** with the following resources:
   - Azure App Service: `boloo-backend-api` (for backend)
   - Azure Static Web Apps: `boloo-web-admin` (for frontend)
   - Azure Database for PostgreSQL: `boloo-database`
   - Azure Resource Group: `boloo-production-rg`

2. **Expo Account** for mobile builds:
   - EAS Build configured
   - Expo API token

3. **GitHub Account** with:
   - Repository admin access
   - Actions enabled

### Initial Setup Steps

1. **Fork or clone the repository**
   ```bash
   git clone https://github.com/your-org/boloo-app.git
   cd boloo-app
   ```

2. **Configure Azure credentials**
   ```bash
   # Create a service principal
   az ad sp create-for-rbac --name "boloo-github-actions" \
     --role contributor \
     --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group} \
     --sdk-auth
   ```

3. **Set up Expo**
   ```bash
   # Install EAS CLI
   npm install -g eas-cli

   # Login and configure
   eas login
   eas build:configure
   ```

## 🔑 GitHub Secrets Configuration

Navigate to **Settings → Secrets and variables → Actions** in your GitHub repository and add the following secrets:

### Required Secrets

#### Azure Backend Deployment
```yaml
AZURE_CREDENTIALS:
  # JSON output from az ad sp create-for-rbac command
  {
    "clientId": "xxx",
    "clientSecret": "xxx",
    "subscriptionId": "xxx",
    "tenantId": "xxx"
  }

AZURE_RESOURCE_GROUP: "boloo-production-rg"
DATABASE_URL: "postgresql://user:pass@boloo-database.postgres.database.azure.com:5432/dbname?sslmode=require"
SECRET_KEY: "your-secret-key-min-32-chars"
```

#### Azure Web Deployment
```yaml
AZURE_STATIC_WEB_APPS_API_TOKEN: "xxx"
AZURE_STATIC_WEB_APPS_STAGING_TOKEN: "xxx"
NEXT_PUBLIC_API_URL: "https://boloo-backend-api.azurewebsites.net"
```

#### Mobile Build (Expo)
```yaml
EXPO_TOKEN: "your-expo-token"
EXPO_PUBLIC_API_URL: "https://api.boloo.app"
```

#### Staging Environment
```yaml
STAGING_DATABASE_URL: "postgresql://user:pass@boloo-database-staging.postgres.database.azure.com:5432/dbname?sslmode=require"
STAGING_SECRET_KEY: "staging-secret-key"
STAGING_API_URL: "https://boloo-backend-api-staging.azurewebsites.net"
```

#### Optional Secrets
```yaml
SLACK_WEBHOOK_URL: "https://hooks.slack.com/services/xxx"  # For notifications
SONAR_TOKEN: "xxx"  # For SonarCloud code quality
SNYK_TOKEN: "xxx"  # For Snyk security scanning
PAT_TOKEN: "xxx"  # Personal Access Token for auto-creating PRs
```

### Environment Variables

Set these in **Settings → Environments** for production and staging:

**Production Environment:**
- `AZURE_WEBAPP_NAME`: boloo-backend-api
- `WEB_APP_URL`: https://boloo.app

**Staging Environment:**
- `AZURE_WEBAPP_NAME`: boloo-backend-api-staging
- `WEB_APP_URL`: https://staging.boloo.app

## 📄 Workflow Details

### 1. test.yml - Continuous Integration Tests

**Triggers:**
- Pull requests to `main` or `develop`
- Push to `develop` branch
- Manual dispatch

**Features:**
- 🔍 Detects changed files (only runs relevant tests)
- 🧪 Runs unit and integration tests
- 📊 Generates coverage reports
- 🔒 Security scanning with Trivy
- 🎯 Code quality analysis with SonarCloud
- 📦 Dependency review for PRs

**Components Tested:**
- **Backend**: pytest with PostgreSQL and Redis services
- **Web**: Jest tests and Next.js build
- **Mobile**: Jest tests and TypeScript checking

**Example Test Run:**
```bash
# Locally run what CI does
cd backend && pytest tests/ -v --cov=.
cd web && npm test -- --ci --coverage
cd mobile && npm test -- --ci --coverage
```

### 2. deploy-backend.yml - Backend Deployment

**Triggers:**
- Push to `main` with changes in `backend/**`
- Manual dispatch with environment selection

**Pipeline Steps:**
1. **Test Job**: Run tests and linting
2. **Build Job**: Create deployment package
3. **Deploy Job**: Deploy to Azure App Service
4. **Migration Job**: Run database migrations
5. **Health Check**: Verify deployment
6. **Rollback Job**: Automatic rollback on failure

**Features:**
- ✅ Automated testing before deployment
- 🔄 Blue-green deployment support
- 🗄️ Automatic database migrations
- ❤️ Health checks post-deployment
- ⏪ Automatic rollback on failure
- 📢 Slack notifications

**Manual Deployment:**
```bash
# Trigger manual deployment
gh workflow run deploy-backend.yml -f environment=production
```

### 3. deploy-web.yml - Web Frontend Deployment

**Triggers:**
- Push to `main` with changes in `web/**`
- Pull requests (preview deployments)
- Manual dispatch

**Pipeline Steps:**
1. Install dependencies with npm cache
2. Run linting and type checking
3. Build Next.js static export
4. Optimize assets (compression, removing source maps)
5. Deploy to Azure Static Web Apps
6. Run Lighthouse performance audit

**Features:**
- 🚀 Static site generation
- 🎨 Asset optimization
- 📱 Preview deployments for PRs
- ⚡ Lighthouse CI integration
- 🗜️ Gzip compression
- 🔒 Security headers configuration

**Configuration File (staticwebapp.config.json):**
```json
{
  "navigationFallback": {
    "rewrite": "/index.html"
  },
  "globalHeaders": {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Strict-Transport-Security": "max-age=31536000"
  }
}
```

### 4. build-mobile.yml - Mobile App Build

**Triggers:**
- Push to `main` with changes in `mobile/**`
- Manual dispatch with platform selection

**Pipeline Steps:**
1. **Test Job**: Run Jest tests
2. **Build Android Job**: Build APK with EAS
3. **Build iOS Job**: Build IPA with EAS (macOS runner)
4. **Release Job**: Create GitHub release with artifacts

**Features:**
- 📱 Multi-platform builds (Android & iOS)
- 🏗️ EAS Build integration
- 📦 Automated GitHub releases
- ✅ Automated testing
- 🔔 Build notifications

**Manual Build:**
```bash
# Build for specific platform
gh workflow run build-mobile.yml -f platform=android -f profile=production
```

### 5. deploy-staging.yml - Staging Deployment

**Triggers:**
- Push to `develop` branch
- Manual dispatch

**Pipeline Steps:**
1. Deploy backend to staging slot
2. Deploy web to staging environment
3. Run end-to-end tests
4. Run smoke tests
5. Send notifications

**Features:**
- 🧪 E2E testing with Playwright
- 🔍 Smoke tests for critical paths
- 🔄 Isolated staging environment
- ✅ Pre-production validation

**Staging URLs:**
- Backend: https://boloo-backend-api-staging.azurewebsites.net
- Web: https://staging.boloo.app

### 6. dependency-update.yml - Dependency Management

**Triggers:**
- Weekly schedule (Monday 9 AM UTC)
- Manual dispatch

**Pipeline Steps:**
1. Update dependencies (Python & npm)
2. Run security audits
3. Check license compliance
4. Create pull requests for updates
5. Auto-merge safe updates

**Features:**
- 🔄 Automated dependency updates
- 🔒 Security vulnerability scanning
- 📜 License compliance checking
- 🤖 Dependabot integration
- 🔀 Auto-merge for patch updates

**Tools Used:**
- npm audit (Node.js)
- Safety (Python)
- Snyk (Multi-language)
- License-checker

## 📊 Status Badges

Add these badges to your README.md:

```markdown
![CI Tests](https://github.com/your-org/boloo-app/workflows/Continuous%20Integration%20Tests/badge.svg)
![Backend Deploy](https://github.com/your-org/boloo-app/workflows/Deploy%20Backend%20to%20Azure/badge.svg)
![Web Deploy](https://github.com/your-org/boloo-app/workflows/Deploy%20Web%20to%20Azure%20Static%20Web%20Apps/badge.svg)
![Mobile Build](https://github.com/your-org/boloo-app/workflows/Build%20Mobile%20App/badge.svg)
[![codecov](https://codecov.io/gh/your-org/boloo-app/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/boloo-app)
```

## 🔍 Monitoring & Observability

### View Workflow Runs

1. Navigate to **Actions** tab in GitHub
2. Select workflow from the left sidebar
3. Click on a specific run to see details

### Checking Logs

```bash
# Using GitHub CLI
gh run list
gh run view [run-id]
gh run view [run-id] --log
```

### Artifacts

Workflows generate artifacts that are stored for specific retention periods:

- **Test Coverage Reports**: 30 days
- **Mobile App Builds**: 30 days
- **Security Audit Results**: 30 days
- **License Reports**: 90 days

## 🚨 Troubleshooting

### Common Issues

#### 1. Deployment Fails with "Unauthorized"

**Solution:**
```bash
# Verify Azure credentials
az login
az account show

# Regenerate service principal if needed
az ad sp create-for-rbac --name "boloo-github-actions" --role contributor --scopes /subscriptions/{id}/resourceGroups/{rg} --sdk-auth
```

#### 2. Tests Fail in CI but Pass Locally

**Common causes:**
- Environment variables missing
- Database connection issues
- Node/Python version mismatch

**Solution:**
```bash
# Check workflow logs
gh run view [run-id] --log

# Ensure local matches CI environment
python --version  # Should match PYTHON_VERSION in workflows
node --version    # Should match NODE_VERSION in workflows
```

#### 3. Mobile Build Fails

**Solution:**
```bash
# Verify Expo token
eas whoami

# Check build status
eas build:list

# Regenerate token if needed
eas login
# Copy new token to GitHub secrets
```

#### 4. Deployment Slots Issues

**Solution:**
```bash
# List deployment slots
az webapp deployment slot list --name boloo-backend-prod --resource-group boloo-resources

# Create slot if missing
az webapp deployment slot create --name boloo-backend-prod --resource-group boloo-resources --slot staging
```

### Getting Help

1. **Check Workflow Logs**: Detailed error messages in GitHub Actions logs
2. **Review Documentation**: Azure, Expo, GitHub Actions docs
3. **Community Support**: GitHub Discussions or Stack Overflow
4. **Open an Issue**: Create issue in repository with workflow logs

## 🔐 Security Best Practices

1. **Never commit secrets**: Use GitHub Secrets exclusively
2. **Rotate credentials regularly**: Update secrets every 90 days
3. **Use least privilege**: Service principals with minimal required permissions
4. **Enable branch protection**: Require PR reviews and status checks
5. **Review dependency updates**: Don't auto-merge major version updates
6. **Monitor security alerts**: Enable Dependabot and security advisories

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Azure App Service Deployment](https://docs.microsoft.com/en-us/azure/app-service/)
- [Azure Static Web Apps](https://docs.microsoft.com/en-us/azure/static-web-apps/)
- [Expo EAS Build](https://docs.expo.dev/build/introduction/)
- [Codecov Integration](https://docs.codecov.com/docs/github-integration)

## 🎯 Next Steps

1. ✅ Configure all required GitHub Secrets
2. ✅ Set up Azure resources
3. ✅ Configure Expo account
4. ✅ Test workflows with manual dispatch
5. ✅ Enable branch protection rules
6. ✅ Set up monitoring and alerts
7. ✅ Document your deployment process
8. ✅ Train team on CI/CD workflows

---

**Last Updated**: 2025-11-22
**Maintainer**: DevOps Team
**Version**: 1.0.0
