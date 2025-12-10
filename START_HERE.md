# 🚀 START HERE - First Time Setup

Follow these steps **in order** to get Boloo running:

---

## Step 1: Start Docker Desktop

1. Open **Docker Desktop** application (look for Docker icon in Applications)
2. Wait for Docker to start completely (whale icon in menu bar should be active)
3. Verify Docker is running by opening Terminal and typing:
   ```bash
   docker info
   ```
   You should see Docker version information (not an error)

**If you don't have Docker Desktop installed:**
- Download from: https://www.docker.com/products/docker-desktop
- Install and start it

---

## Step 2: Navigate to Project Directory

In Terminal, run:
```bash
cd "/Users/diptendu/boloo app/boloo-app"
```

**Note**: The quotes are important because of the space in "boloo app"!

---

## Step 3: Run the Restart Script

```bash
./restart.sh
```

This will:
- ✅ Install Python dependencies
- ✅ Start PostgreSQL, Redis, MinIO (Docker)
- ✅ Create database tables
- ✅ Load seed data (131 entities + 50+ issue types)
- ✅ Start backend API (daemon mode, port 8000)
- ✅ Start web admin console (daemon mode, port 3000)

**First run takes 3-5 minutes** to install all dependencies.

---

## Step 4: Verify Services Are Running

```bash
pm2 status
```

You should see:
- `boloo-backend` - **online** ✅
- `boloo-web` - **online** ✅

Check Docker services:
```bash
docker-compose ps
```

You should see:
- `boloo-postgres` - **Up** ✅
- `boloo-redis` - **Up** ✅
- `boloo-minio` - **Up** ✅

---

## Step 5: Open Web Admin Console

**URL**: http://localhost:3000

**Test Monitoring Dashboard**:
1. Go to http://localhost:3000/monitoring
2. You should see all systems with green ✅ indicators
3. Watch it auto-refresh every 60 seconds!

**Test Backend API**:
- Health check: http://localhost:8000/health
- API docs: http://localhost:8000/docs

---

## ⚠️ Troubleshooting

### Error: "Cannot connect to Docker daemon"
**Solution**: Start Docker Desktop application

### Error: "Port 8000 already in use"
**Solution**:
```bash
lsof -ti:8000 | xargs kill -9
./restart.sh
```

### Error: "Port 3000 already in use"
**Solution**:
```bash
lsof -ti:3000 | xargs kill -9
./restart.sh
```

### Services not starting
**Solution**: Check logs
```bash
pm2 logs boloo-backend
pm2 logs boloo-web
docker-compose logs postgres
```

---

## 🔄 Daily Usage

After first-time setup, you only need:

```bash
# Start Docker Desktop (if not running)

# Navigate to project
cd "/Users/diptendu/boloo app/boloo-app"

# Restart all services
./restart.sh
```

Services will run in background (daemon mode). You can close the terminal!

---

## 🛑 Stopping Services

```bash
pm2 stop all
docker-compose down
```

---

## 📖 Next Steps

Once everything is running:
1. ✅ Test web console: http://localhost:3000
2. ✅ Test monitoring: http://localhost:3000/monitoring
3. ✅ Test backend API: http://localhost:8000/docs
4. 📱 Build Android mobile app (next phase)

See `QUICK_START.md` for detailed testing instructions.
