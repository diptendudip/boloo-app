# CI/CD Pipeline Guide - Bultoo App

## Overview
Automated deployment pipeline using GitHub Actions for backend (FastAPI) and mobile (React Native) apps.

## Table of Contents
1. [GitHub Actions Setup](#github-actions-setup)
2. [Backend Deployment Pipeline](#backend-deployment-pipeline)
3. [Mobile Build Pipeline](#mobile-build-pipeline)
4. [Environment Variables Management](#environment-variables-management)
5. [Database Migration Strategy](#database-migration-strategy)
6. [Testing Automation](#testing-automation)

---

## GitHub Actions Setup

### 1. Enable GitHub Actions

1. Go to repository settings
2. Navigate to "Actions" → "General"
3. Enable "Allow all actions and reusable workflows"

### 2. Create Workflow Directory

```bash
# Create .github/workflows directory
mkdir -p .github/workflows
```

---

## Backend Deployment Pipeline

### Complete Backend CI/CD Workflow

Create `.github/workflows/backend-deploy.yml`:

```yaml
name: Backend CI/CD Pipeline

on:
  push:
    branches:
      - main
      - develop
    paths:
      - 'backend/**'
      - '.github/workflows/backend-deploy.yml'
  pull_request:
    branches:
      - main
    paths:
      - 'backend/**'

env:
  AZURE_WEBAPP_NAME: bultoo-api
  AZURE_RESOURCE_GROUP: bultoo-rg
  PYTHON_VERSION: '3.11'

jobs:
  # Job 1: Linting and Code Quality
  lint:
    name: Lint and Code Quality
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          python -m pip install --upgrade pip
          pip install flake8 black mypy pylint
          pip install -r requirements.txt

      - name: Run Black (formatting check)
        run: |
          cd backend
          black --check .

      - name: Run Flake8 (linting)
        run: |
          cd backend
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

      - name: Run MyPy (type checking)
        run: |
          cd backend
          mypy . --ignore-missing-imports || true

  # Job 2: Testing
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    needs: lint

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_bultoo_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          cd backend
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio httpx

      - name: Run tests with coverage
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_bultoo_db
          SECRET_KEY: test-secret-key-for-ci
        run: |
          cd backend
          pytest --cov=. --cov-report=xml --cov-report=html --cov-report=term

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: backend/coverage.xml
          flags: backend
          name: backend-coverage

      - name: Archive coverage report
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: backend/htmlcov/

  # Job 3: Security Scanning
  security:
    name: Security Scan
    runs-on: ubuntu-latest
    needs: lint

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Bandit (security linter)
        run: |
          pip install bandit
          cd backend
          bandit -r . -f json -o bandit-report.json || true

      - name: Run Safety (dependency vulnerability check)
        run: |
          pip install safety
          cd backend
          safety check --json || true

      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: backend/bandit-report.json

  # Job 4: Build Docker Image (Optional)
  build:
    name: Build Application
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Create deployment package
        run: |
          cd backend
          zip -r ../deploy.zip . -x "*.git*" -x "*__pycache__*" -x "*.env*" -x "*venv*" -x "*tests*"

      - name: Upload build artifact
        uses: actions/upload-artifact@v3
        with:
          name: deployment-package
          path: deploy.zip

  # Job 5: Database Migration Check
  migration-check:
    name: Check Database Migrations
    runs-on: ubuntu-latest
    needs: test

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: migration_test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run migrations
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/migration_test_db
        run: |
          cd backend
          alembic upgrade head

      - name: Check migration status
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/migration_test_db
        run: |
          cd backend
          alembic current

  # Job 6: Deploy to Azure
  deploy:
    name: Deploy to Azure
    runs-on: ubuntu-latest
    needs: [build, migration-check]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://api.bultoo.com

    steps:
      - name: Download build artifact
        uses: actions/download-artifact@v3
        with:
          name: deployment-package

      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Deploy to Azure Web App
        uses: azure/webapps-deploy@v2
        with:
          app-name: ${{ env.AZURE_WEBAPP_NAME }}
          package: deploy.zip

      - name: Run Database Migrations on Azure
        run: |
          az webapp ssh --name ${{ env.AZURE_WEBAPP_NAME }} \
            --resource-group ${{ env.AZURE_RESOURCE_GROUP }} \
            --command "cd /home/site/wwwroot && python -m alembic upgrade head"

      - name: Restart Azure Web App
        run: |
          az webapp restart \
            --name ${{ env.AZURE_WEBAPP_NAME }} \
            --resource-group ${{ env.AZURE_RESOURCE_GROUP }}

      - name: Health Check
        run: |
          sleep 30
          curl -f https://api.bultoo.com/health || exit 1

      - name: Azure Logout
        run: az logout

  # Job 7: Notification
  notify:
    name: Send Notifications
    runs-on: ubuntu-latest
    needs: deploy
    if: always()

    steps:
      - name: Send deployment status
        run: |
          echo "Deployment status: ${{ needs.deploy.result }}"
          # Add Slack/Discord/Email notification here
```

---

## Mobile Build Pipeline

Create `.github/workflows/mobile-build.yml`:

```yaml
name: Mobile App CI/CD

on:
  push:
    branches:
      - main
      - develop
    paths:
      - 'mobile/**'
      - '.github/workflows/mobile-build.yml'
  pull_request:
    branches:
      - main
    paths:
      - 'mobile/**'

jobs:
  # Job 1: Lint and Type Check
  lint:
    name: Lint Mobile App
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: mobile/package-lock.json

      - name: Install dependencies
        run: |
          cd mobile
          npm ci

      - name: Run ESLint
        run: |
          cd mobile
          npm run lint

      - name: Run TypeScript check
        run: |
          cd mobile
          npm run type-check || true

  # Job 2: Test
  test:
    name: Test Mobile App
    runs-on: ubuntu-latest
    needs: lint

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: mobile/package-lock.json

      - name: Install dependencies
        run: |
          cd mobile
          npm ci

      - name: Run tests
        run: |
          cd mobile
          npm test -- --coverage --watchAll=false

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: mobile/coverage/coverage-final.json
          flags: mobile
          name: mobile-coverage

  # Job 3: Build APK (Preview)
  build-preview:
    name: Build Preview APK
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' && (github.ref == 'refs/heads/develop' || github.ref == 'refs/heads/main')

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: mobile/package-lock.json

      - name: Setup Expo
        uses: expo/expo-github-action@v8
        with:
          expo-version: latest
          eas-version: latest
          token: ${{ secrets.EXPO_TOKEN }}

      - name: Install dependencies
        run: |
          cd mobile
          npm ci

      - name: Increment version code
        run: |
          cd mobile
          node scripts/increment-version.js

      - name: Build APK
        run: |
          cd mobile
          eas build --platform android --profile preview --non-interactive

      - name: Upload APK artifact
        uses: actions/upload-artifact@v3
        with:
          name: app-preview.apk
          path: mobile/*.apk

  # Job 4: Build Production AAB
  build-production:
    name: Build Production AAB
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    environment:
      name: production

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: mobile/package-lock.json

      - name: Setup Expo
        uses: expo/expo-github-action@v8
        with:
          expo-version: latest
          eas-version: latest
          token: ${{ secrets.EXPO_TOKEN }}

      - name: Install dependencies
        run: |
          cd mobile
          npm ci

      - name: Build AAB
        run: |
          cd mobile
          eas build --platform android --profile production --non-interactive

      - name: Submit to Play Store (Internal Testing)
        run: |
          cd mobile
          eas submit --platform android --latest --track internal
```

---

## Environment Variables Management

### 1. GitHub Secrets Setup

Add these secrets in GitHub repository settings:

```bash
# Azure Credentials
AZURE_CREDENTIALS='{"clientId":"xxx","clientSecret":"xxx","subscriptionId":"xxx","tenantId":"xxx"}'

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Application
SECRET_KEY=your-secret-key

# Azure Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...

# Expo/EAS
EXPO_TOKEN=your-expo-token

# Optional: Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx
```

### 2. Azure Credentials Generation

```bash
# Create service principal for GitHub Actions
az ad sp create-for-rbac \
  --name "github-actions-bultoo" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/bultoo-rg \
  --sdk-auth

# Output JSON - copy entire output to AZURE_CREDENTIALS secret
```

### 3. Environment-Specific Variables

Create `.github/workflows/environments.yml`:

```yaml
name: Environment Configuration

on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string

jobs:
  configure:
    runs-on: ubuntu-latest
    steps:
      - name: Set environment variables
        run: |
          if [ "${{ inputs.environment }}" == "production" ]; then
            echo "API_URL=https://api.bultoo.com" >> $GITHUB_ENV
            echo "DATABASE_NAME=bultoo_db" >> $GITHUB_ENV
          elif [ "${{ inputs.environment }}" == "staging" ]; then
            echo "API_URL=https://staging-api.bultoo.com" >> $GITHUB_ENV
            echo "DATABASE_NAME=bultoo_staging_db" >> $GITHUB_ENV
          else
            echo "API_URL=http://localhost:8000" >> $GITHUB_ENV
            echo "DATABASE_NAME=bultoo_dev_db" >> $GITHUB_ENV
          fi
```

---

## Database Migration Strategy

### 1. Alembic Configuration

Create `alembic.ini` in backend:

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### 2. Migration Scripts

Create migration script template:

```python
# alembic/versions/001_initial.py
"""Initial migration

Revision ID: 001
Revises:
Create Date: 2025-01-19

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

def downgrade() -> None:
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
```

### 3. Automated Migration Workflow

Create `.github/workflows/database-migration.yml`:

```yaml
name: Database Migration

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        type: choice
        options:
          - development
          - staging
          - production

jobs:
  migrate:
    name: Run Database Migrations
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run migrations
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          cd backend
          alembic upgrade head

      - name: Verify migration
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          cd backend
          alembic current
```

---

## Testing Automation

### Backend Tests

Create `backend/tests/test_api.py`:

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_create_user():
    response = client.post(
        "/api/v1/users/",
        json={"email": "test@example.com", "password": "testpass123"}
    )
    assert response.status_code == 201
    assert "id" in response.json()
```

### Mobile Tests

Create `mobile/tests/App.test.js`:

```javascript
import React from 'react';
import { render } from '@testing-library/react-native';
import App from '../App';

describe('App', () => {
  it('renders correctly', () => {
    const { getByText } = render(<App />);
    expect(getByText('Bultoo')).toBeTruthy();
  });
});
```

---

## Monitoring and Rollback

### Deployment Status Monitoring

```yaml
# Add to deploy job
- name: Monitor deployment
  run: |
    for i in {1..10}; do
      STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.bultoo.com/health)
      if [ $STATUS -eq 200 ]; then
        echo "Deployment successful!"
        exit 0
      fi
      echo "Waiting for deployment... ($i/10)"
      sleep 10
    done
    echo "Deployment failed!"
    exit 1
```

### Automatic Rollback

```yaml
- name: Rollback on failure
  if: failure()
  run: |
    az webapp deployment slot swap \
      --name ${{ env.AZURE_WEBAPP_NAME }} \
      --resource-group ${{ env.AZURE_RESOURCE_GROUP }} \
      --slot staging \
      --target-slot production
```

---

## Cost Optimization

GitHub Actions free tier:
- 2,000 minutes/month for private repos
- Unlimited for public repos

Tips to optimize:
1. Use caching for dependencies
2. Run jobs in parallel
3. Use workflow conditions to skip unnecessary jobs
4. Cache Docker layers

---

## Next Steps

1. ✅ Set up GitHub secrets
2. ✅ Create Azure service principal
3. ✅ Test workflow on develop branch
4. ✅ Configure branch protection rules
5. ✅ Set up status checks
6. ✅ Enable auto-merge for green PRs

---

## Resources

- [GitHub Actions Documentation](https://docs.github.com/actions)
- [Azure Web Apps Deploy Action](https://github.com/Azure/webapps-deploy)
- [Expo GitHub Actions](https://github.com/expo/expo-github-action)
