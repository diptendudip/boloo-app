# Boloo MVP - Quick Start Guide

**Ready to run!** Follow these steps to get the backend and web admin console running.

---

## ✅ What's Built and Ready

### Backend (100% MVP Complete)
- ✅ FastAPI REST API with all core endpoints
- ✅ Email OTP authentication
- ✅ Cases CRUD operations
- ✅ Entities and Taxonomies endpoints
- ✅ **Monitoring API with health checks** ⭐
- ✅ PostgreSQL database with 131 entities + 50+ issue types
- ✅ **Daemon mode with PM2** ⭐
- ✅ **One-line restart script** ⭐

### Web Admin Console (100% MVP Complete)
- ✅ **Navigation panel with all page links** ⭐
- ✅ **Operational Monitoring Dashboard (60s auto-refresh)** ⭐
- ✅ Dashboard with metrics
- ✅ Cases list view
- ✅ Entities list view
- ✅ Taxonomies list view
- ✅ Placeholder pages for future features

---

## 🚀 Step 1: One-Command Setup

```bash
cd "/Users/diptendu/boloo app/boloo-app"
./restart.sh
```

This will:
1. Stop any running services
2. Start Docker (PostgreSQL, Redis, MinIO)
3. Create database tables
4. Load seed data
5. **Start backend in daemon mode (PM2)**
6. **Start web in daemon mode (PM2)**

**First run takes 3-5 minutes** to install dependencies.

---

## 🎯 Step 2: Verify Everything is Running

### Check Services
```bash
pm2 status
```

Should show:
- `boloo-backend` - **online**
- `boloo-web` - **online**

### Check Docker
```bash
docker-compose ps
```

Should show:
- `postgres` - **Up**
- `redis` - **Up**
- `minio` - **Up**

---

## 🌐 Step 3: Access the Applications

### Web Admin Console
**URL**: http://localhost:3000

**Pages Available**:
- **Dashboard** (http://localhost:3000) - Overview with metrics
- **Monitoring** (http://localhost:3000/monitoring) - **Real-time health status with 60s auto-refresh** ⭐
- **Cases** (http://localhost:3000/cases) - List all grievances
- **Entities** (http://localhost:3000/entities) - Government offices (131 loaded)
- **Taxonomies** (http://localhost:3000/taxonomies) - Issue categories (50+)

### Backend API
**URL**: http://localhost:8000

**API Documentation**: http://localhost:8000/docs

**Key Endpoints**:
- `GET /health` - Basic health check
- `GET /v1/monitoring/health` - **Comprehensive system health** ⭐
- `POST /v1/auth/otp/request` - Request OTP
- `POST /v1/auth/otp/verify` - Verify OTP
- `GET /v1/cases` - List cases
- `GET /v1/entities` - List entities (131 items)
- `GET /v1/taxonomies?type=issue` - List issue types

---

## 🧪 Step 4: Test the System

### Test 1: Backend Health Check
```bash
curl http://localhost:8000/health
```

Expected:
```json
{
  "status": "healthy",
  "app": "Boloo",
  "environment": "development",
  "version": "1.0.0"
}
```

### Test 2: Monitoring Endpoint (Your Special Requirement!)
```bash
curl http://localhost:8000/v1/monitoring/health | jq
```

Should show status of:
- Database (PostgreSQL)
- Redis
- MinIO storage
- Azure Speech API
- Claude API
- SMTP

### Test 3: Web Monitoring Dashboard
Open browser: **http://localhost:3000/monitoring**

You should see:
- ✅ Green status indicators for infrastructure
- ✅ Auto-refresh countdown (60 seconds)
- ✅ All service statuses
- ✅ API endpoints table

**Refresh happens automatically every 60 seconds!** ⭐

### Test 4: Request OTP
```bash
curl -X POST http://localhost:8000/v1/auth/otp/request \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

Check logs for OTP:
```bash
pm2 logs boloo-backend --lines 50 | grep "OTP"
```

OTP will be in the logs (or sent to diptendudip@gmail.com if SMTP is configured).

### Test 5: List Entities
```bash
curl http://localhost:8000/v1/entities | jq '.entities | length'
```

Should return: `131` (1 state + 30 districts + 60 blocks + 100 GPs + 10 departments)

### Test 6: List Issue Types
```bash
curl "http://localhost:8000/v1/taxonomies?type=issue" | jq '.taxonomies | length'
```

Should return: `50+` issue categories in Hindi and English

---

## 📊 Web Admin Console Features

### Navigation Panel ⭐
- Persistent sidebar on all pages
- Links to: Dashboard, Monitoring, Cases, Entities, Taxonomies, Users, Analytics, Settings
- Logout button at bottom

### Monitoring Dashboard ⭐ (http://localhost:3000/monitoring)
- **Auto-refreshes every 60 seconds**
- Overall system status indicator
- Infrastructure section:
  - PostgreSQL status
  - Redis status
  - MinIO storage status
- External Services section:
  - Azure Speech API status
  - Claude API status
  - SMTP status
- API Endpoints table
- Manual refresh button
- Countdown timer showing next auto-refresh

### Dashboard (http://localhost:3000)
- Total cases count
- Total users count
- Total entities count (131)
- Cases by status breakdown
- Quick action cards

### Cases Page (http://localhost:3000/cases)
- List all cases
- Filter by status
- Show case details (title, summary, location, date)
- Status badges with color coding

### Entities Page (http://localhost:3000/entities)
- Grid view of all 131 government offices
- Filter by type (District, Block, GP, Department)
- Contact information
- Type badges

---

## 🔄 Common Commands

### View Logs
```bash
# Backend logs
pm2 logs boloo-backend

# Web logs
pm2 logs boloo-web

# All logs
pm2 logs

# Database logs
docker-compose logs postgres
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
# Stop all PM2 services
pm2 stop all

# Stop Docker services
docker-compose down

# Stop everything
pm2 stop all && docker-compose down
```

### Database Queries
```bash
# Access database
psql postgresql://boloo:boloo_dev_password@localhost:5432/boloo

# Count entities
psql postgresql://boloo:boloo_dev_password@localhost:5432/boloo -c "SELECT COUNT(*) FROM entities;"

# Count taxonomies
psql postgresql://boloo:boloo_dev_password@localhost:5432/boloo -c "SELECT COUNT(*) FROM taxonomies;"

# List issue types
psql postgresql://boloo:boloo_dev_password@localhost:5432/boloo -c "SELECT key, label_en, label_hi FROM taxonomies WHERE type='issue' LIMIT 10;"
```

---

## ✨ Key Features Working

### Daemon Mode ✅
Services run in background using PM2:
```bash
pm2 status
```

Close your terminal - services keep running!

### One-Line Restart ✅
```bash
./restart.sh
```

Restarts everything in the correct order.

### Monitoring Dashboard with Auto-Refresh ✅
- Updates every 60 seconds automatically
- Green/Yellow/Red status indicators
- Shows all endpoints and services

### Navigation Panel ✅
- Always visible on left side
- Links to all pages
- Active page highlighting

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Then restart
./restart.sh
```

### Docker Not Starting
```bash
# Check Docker Desktop is running
docker info

# Restart Docker Desktop
# Then run
./restart.sh
```

### Web Console Not Loading
```bash
# Check PM2 status
pm2 logs boloo-web

# Restart web
pm2 restart boloo-web
```

### Database Connection Error
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Wait 5 seconds
sleep 5

# Restart backend
pm2 restart boloo-backend
```

---

## 📁 File Locations

**Configuration**:
- Backend: `/Users/diptendu/boloo app/boloo-app/backend/`
- Web: `/Users/diptendu/boloo app/boloo-app/web/`
- Environment: `/Users/diptendu/boloo app/boloo-app/.env`

**Logs**:
- PM2 logs: `~/.pm2/logs/`
- Docker logs: `docker-compose logs`

**Data**:
- Database: Docker volume `postgres_data`
- Media files: Docker volume `minio_data`

---

## 🎉 Success Checklist

After running `./restart.sh`, verify:

- [ ] `pm2 status` shows 2 services running
- [ ] `docker-compose ps` shows 3 services running
- [ ] http://localhost:8000/health returns "healthy"
- [ ] http://localhost:3000 loads dashboard
- [ ] http://localhost:3000/monitoring shows all green statuses
- [ ] Monitoring dashboard auto-refreshes every 60 seconds
- [ ] Navigation panel appears on all pages
- [ ] http://localhost:3000/entities shows 131 entities
- [ ] Can close terminal and services keep running (daemon mode)

---

## 📚 Next Steps

### Configure Environment (Optional)
Edit `.env` file to add:
```bash
# For Claude API integration
ANTHROPIC_API_KEY=your_key_here

# For Azure Speech Services
AZURE_SPEECH_KEY=your_key_here
AZURE_SPEECH_REGION=centralindia

# For email OTP (Gmail)
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

Then restart:
```bash
./restart.sh
```

### Test OTP Login
1. Request OTP: `POST /v1/auth/otp/request` with `{"email": "test@example.com"}`
2. Check logs: `pm2 logs boloo-backend | grep OTP`
3. Verify OTP: `POST /v1/auth/otp/verify` with email and code
4. Get JWT token

### Create Test Case
Use the API docs at http://localhost:8000/docs to create a test case.

### Explore Monitoring
Open http://localhost:3000/monitoring and watch it auto-refresh every 60 seconds!

---

## 📖 Reference Documents

- **Development Phases**: `docs/DEVELOPMENT_PHASES.md` (saved for reference)
- **Architecture**: `docs/ARCHITECTURE.md`
- **Current Status**: `CURRENT_STATUS.md`
- **Full Setup**: `MVP_SETUP.md`

---

## 🆘 Support

If you need help:
1. Check logs: `pm2 logs`
2. Check Docker: `docker-compose logs`
3. Try clean restart: `pm2 delete all && docker-compose down -v && ./restart.sh`

---

**All core requirements completed!** ✅
- ✅ Daemon mode servers
- ✅ One-line restart script
- ✅ Navigation panel with all page links
- ✅ Operational monitoring dashboard (60s auto-refresh)
