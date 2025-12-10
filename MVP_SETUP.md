# Boloo MVP Setup Guide

This guide will help you get the Boloo MVP up and running on your Mac.

## Prerequisites

Before starting, ensure you have the following installed:

1. **Docker Desktop for Mac** - [Download](https://www.docker.com/products/docker-desktop)
2. **Node.js 18+** - [Download](https://nodejs.org/) or use `brew install node`
3. **Python 3.11+** - Should be pre-installed, or `brew install python@3.11`
4. **PM2** (Process Manager) - Will be installed by restart script
5. **PostgreSQL Client** (psql) - `brew install postgresql`

## Step 1: Environment Configuration

1. Navigate to the project directory:
```bash
cd "/Users/diptendu/boloo app/boloo-app"
```

2. Copy the environment template:
```bash
cp .env.example .env
```

3. Edit `.env` and configure:
```bash
# Required for MVP:
ANTHROPIC_API_KEY=your_claude_api_key_here

# Optional (for email OTP):
SMTP_USER=your_gmail@gmail.com
SMTP_PASSWORD=your_gmail_app_password

# Optional (for Azure Speech):
AZURE_SPEECH_KEY=your_azure_key
AZURE_SPEECH_REGION=centralindia
```

**Note**: For Phase 1, SMTP is optional. OTPs will be logged to console if not configured.

## Step 2: One-Command Setup

Run the restart script to set up everything:

```bash
./restart.sh
```

This script will:
1. Stop any running services
2. Start Docker services (PostgreSQL, Redis, MinIO)
3. Create database tables
4. Load seed data (entities + taxonomies)
5. Start backend API in daemon mode (PM2)
6. Start web admin console in daemon mode (PM2)

**First run may take 3-5 minutes** to install dependencies.

## Step 3: Verify Installation

After the script completes, verify services are running:

```bash
pm2 status
```

You should see:
- `boloo-backend` - running
- `boloo-web` - running

Check Docker services:
```bash
docker-compose ps
```

You should see:
- `postgres` - Up
- `redis` - Up
- `minio` - Up

## Step 4: Access the Application

### Backend API
- **URL**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Web Admin Console
- **URL**: http://localhost:3000
- **Monitoring Dashboard**: http://localhost:3000/monitoring

### Docker Services
- **MinIO Console**: http://localhost:9001 (minioadmin / minioadmin)
- **PostgreSQL**: localhost:5432 (boloo / boloo_dev_password)
- **Redis**: localhost:6379

## Step 5: Test the MVP

### Test 1: API Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "app": "Boloo",
  "environment": "development"
}
```

### Test 2: Request OTP
```bash
curl -X POST http://localhost:8000/v1/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

Check backend logs for OTP:
```bash
pm2 logs boloo-backend --lines 20
```

### Test 3: List Taxonomies
```bash
curl http://localhost:8000/v1/taxonomies?type=issue
```

### Test 4: Access Monitoring Dashboard
Open browser: http://localhost:3000/monitoring

Should show status of all endpoints and services.

## Step 6: Create Admin User (Optional)

To create an admin user for testing:

```bash
psql postgresql://boloo:boloo_dev_password@localhost:5432/boloo << EOF
UPDATE users SET role = 'admin' WHERE email = 'your_email@example.com';
EOF
```

## Common Commands

### View Logs
```bash
# Backend logs
pm2 logs boloo-backend

# Web logs
pm2 logs boloo-web

# Docker logs
docker-compose logs -f postgres
```

### Restart Services
```bash
# Restart everything
./restart.sh

# Restart just backend
pm2 restart boloo-backend

# Restart just web
pm2 restart boloo-web
```

### Stop Services
```bash
# Stop PM2 services
pm2 stop all

# Stop Docker services
docker-compose down

# Stop everything
pm2 stop all && docker-compose down
```

### Database Access
```bash
# Access PostgreSQL
psql postgresql://boloo:boloo_dev_password@localhost:5432/boloo

# View tables
psql postgresql://boloo:boloo_dev_password@localhost:5432/boloo -c "\dt"

# Count cases
psql postgresql://boloo:boloo_dev_password@localhost:5432/boloo -c "SELECT COUNT(*) FROM cases;"
```

## Troubleshooting

### Issue: Docker not starting
```bash
# Check Docker Desktop is running
docker info

# Restart Docker Desktop
# Go to Docker Desktop app > Restart
```

### Issue: Port already in use
```bash
# Check what's using port 8000
lsof -ti:8000

# Kill process
kill -9 $(lsof -ti:8000)

# Then restart
./restart.sh
```

### Issue: Database connection failed
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Restart just PostgreSQL
docker-compose restart postgres

# Wait 5 seconds then restart backend
sleep 5 && pm2 restart boloo-backend
```

### Issue: PM2 not found
```bash
# Install PM2
npm install -g pm2

# Then restart
./restart.sh
```

### Issue: Python dependencies failed
```bash
cd backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..
pm2 restart boloo-backend
```

## Next Steps (After MVP is Running)

1. **Test OTP Login**: Use the web admin to login with email OTP
2. **Create a Test Case**: Use the API to create a test grievance
3. **View Monitoring Dashboard**: Check all services are healthy
4. **Set up Android App**: Follow mobile/README.md
5. **Configure Azure Speech**: Add credentials to .env for voice transcription

## Development Workflow

### Making Backend Changes
```bash
cd backend
source venv/bin/activate
# Make your changes
pm2 restart boloo-backend
pm2 logs boloo-backend
```

### Making Web Changes
```bash
cd web
# Make your changes
pm2 restart boloo-web
pm2 logs boloo-web
```

### Database Migrations
```bash
cd backend
source venv/bin/activate
python3 << EOF
from app.database import engine, Base
from app.models import *
Base.metadata.create_all(bind=engine)
EOF
```

## Daemon Mode (Running in Background)

The restart script automatically starts services in daemon mode using PM2:

- **Backend** runs independently of terminal
- **Web** runs independently of terminal
- **Docker services** run as containers

You can close your terminal and services will continue running.

To check status:
```bash
pm2 status
docker-compose ps
```

To stop when done:
```bash
pm2 stop all
docker-compose down
```

## File Locations

- **Logs**: `~/.pm2/logs/`
- **Database Data**: Docker volume `postgres_data`
- **Media Files**: Docker volume `minio_data`
- **Backend Code**: `backend/app/`
- **Web Code**: `web/`

## Support

If you encounter issues:
1. Check logs: `pm2 logs`
2. Check Docker: `docker-compose logs`
3. Verify ports are free: `lsof -ti:8000 -ti:3000`
4. Try clean restart: `pm2 delete all && docker-compose down -v && ./restart.sh`

## Success Criteria

MVP is working when:
- ✅ `./restart.sh` completes without errors
- ✅ `pm2 status` shows 2 services running
- ✅ `docker-compose ps` shows 3 services running
- ✅ http://localhost:8000/health returns "healthy"
- ✅ http://localhost:3000 loads admin interface
- ✅ http://localhost:3000/monitoring shows all services green

---

**Reference**: See `docs/DEVELOPMENT_PHASES.md` for full development roadmap.
