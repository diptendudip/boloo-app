# Quick Start Guide - GitHub Actions CI/CD

Get your CI/CD pipeline running in **3 simple steps**!

## ⚡ Step 1: Add Required Secrets (5 minutes)

```bash
# Navigate to: Settings → Secrets and variables → Actions
# Click "New repository secret" and add:

1. AZURE_CREDENTIALS - Get this from:
   az ad sp create-for-rbac --name "boloo-github-actions" \
     --role contributor \
     --scopes /subscriptions/{id}/resourceGroups/{rg} \
     --sdk-auth

2. DATABASE_URL - Format: postgresql://user:pass@host:5432/dbname

3. SECRET_KEY - Generate with: openssl rand -hex 32

4. AZURE_STATIC_WEB_APPS_API_TOKEN - From Azure Portal

5. EXPO_TOKEN - From https://expo.dev/accounts/[account]/settings/access-tokens
```

## 🧪 Step 2: Test the Setup (2 minutes)

```bash
# Run the verification workflow
gh workflow run verify-setup.yml

# Check results
gh run list --workflow=verify-setup.yml
gh run view --log
```

## 🚀 Step 3: Deploy! (1 minute)

```bash
# Create a test PR to trigger CI
git checkout -b test/ci-pipeline
echo "# Test" >> README.md
git add . && git commit -m "test: CI pipeline"
git push origin test/ci-pipeline
gh pr create --title "Test CI" --body "Testing workflows"

# Watch it work!
gh pr checks
```

## ✅ What You Get

- ✨ Automated testing on every PR
- 🚀 Automated deployments to Azure
- 📱 Mobile app builds with EAS
- 🔒 Security scanning
- 📊 Code coverage reports
- 🔔 Deployment notifications

## 📖 Need More Help?

- **Full Setup Guide**: See `/docs/CICD_SETUP_GUIDE.md`
- **All Workflows**: See `.github/workflows/README.md`
- **Secrets Template**: See `.github/workflows/secrets-template.yml`

## 🎯 Quick Commands

```bash
# Deploy backend to staging
gh workflow run deploy-backend.yml -f environment=staging

# Build mobile app
gh workflow run build-mobile.yml -f platform=android

# Run all tests
gh workflow run test.yml

# List all workflows
gh workflow list

# View recent runs
gh run list --limit 10
```

That's it! You're ready to ship! 🎉
