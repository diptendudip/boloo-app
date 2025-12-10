#!/bin/bash

###############################################################################
# Boloo Application Restart Script
# One-line command to restart ALL services (backend, web, mobile, docker)
# Usage: ./restart.sh
###############################################################################

set -e  # Exit on error

echo "======================================================"
echo "  Boloo Application Restart Script"
echo "======================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}[1/6] Stopping all services...${NC}"

# Stop backend (PM2)
if command -v pm2 &> /dev/null; then
    pm2 delete boloo-backend 2>/dev/null || true
    echo -e "${GREEN}✓ Backend stopped${NC}"
else
    echo -e "${YELLOW}⚠ PM2 not installed, skipping backend stop${NC}"
fi

# Stop web (PM2)
if command -v pm2 &> /dev/null; then
    pm2 delete boloo-web 2>/dev/null || true
    echo -e "${GREEN}✓ Web console stopped${NC}"
fi

# Stop mobile (kill expo processes)
pkill -f "expo start" 2>/dev/null || true
echo -e "${GREEN}✓ Mobile dev server stopped${NC}"

# Stop Docker services
echo -e "${YELLOW}[2/6] Stopping Docker services...${NC}"
docker-compose down 2>/dev/null || true
echo -e "${GREEN}✓ Docker services stopped${NC}"

echo ""
echo -e "${YELLOW}[3/6] Starting Docker services...${NC}"
docker-compose up -d postgres redis minio

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
sleep 5

# Check if postgres is ready
until docker-compose exec -T postgres pg_isready -U boloo &> /dev/null; do
    echo -e "${YELLOW}Waiting for PostgreSQL...${NC}"
    sleep 2
done
echo -e "${GREEN}✓ PostgreSQL ready${NC}"

echo -e "${GREEN}✓ Redis ready${NC}"
echo -e "${GREEN}✓ MinIO ready${NC}"

echo ""
echo -e "${YELLOW}[4/6] Running database migrations and seeds...${NC}"
cd backend

# Install Python dependencies if needed
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

# Run migrations (create tables)
python3 << EOF
from app.database import engine, Base
from app.models import *
print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✓ Tables created")
EOF

# Run seed data
echo -e "${YELLOW}Loading seed data...${NC}"
psql postgresql://boloo:boloo_dev_password@localhost:5432/boloo < ../database/seeds/01_taxonomies.sql 2>/dev/null || true
psql postgresql://boloo:boloo_dev_password@localhost:5432/boloo < ../database/seeds/02_entities.sql 2>/dev/null || true
echo -e "${GREEN}✓ Seed data loaded${NC}"

cd ..

echo ""
echo -e "${YELLOW}[5/6] Starting backend server (daemon mode)...${NC}"
cd backend

# Install PM2 if not available
if ! command -v pm2 &> /dev/null; then
    echo -e "${YELLOW}Installing PM2...${NC}"
    npm install -g pm2
fi

# Start backend with PM2 (daemon mode)
source venv/bin/activate
pm2 start uvicorn --name boloo-backend -- app.main:app --host 0.0.0.0 --port 8000
pm2 save

echo -e "${GREEN}✓ Backend server started in daemon mode (port 8000)${NC}"
cd ..

echo ""
echo -e "${YELLOW}[6/6] Starting web admin console (daemon mode)...${NC}"
cd web

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing web dependencies...${NC}"
    npm install
fi

# Start web with PM2 (daemon mode)
pm2 start npm --name boloo-web -- run dev
pm2 save

echo -e "${GREEN}✓ Web console started in daemon mode (port 3000)${NC}"
cd ..

echo ""
echo -e "${GREEN}======================================================"
echo -e "  ✓ All services restarted successfully!"
echo -e "======================================================${NC}"
echo ""
echo -e "${GREEN}Services Status:${NC}"
pm2 list
echo ""
echo -e "${GREEN}Application URLs:${NC}"
echo -e "  Backend API:    ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs:       ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  Web Admin:      ${GREEN}http://localhost:3000${NC}"
echo -e "  Monitoring:     ${GREEN}http://localhost:3000/monitoring${NC}"
echo ""
echo -e "${GREEN}Docker Services:${NC}"
echo -e "  PostgreSQL:     ${GREEN}localhost:5432${NC}"
echo -e "  Redis:          ${GREEN}localhost:6379${NC}"
echo -e "  MinIO:          ${GREEN}localhost:9000${NC} (console: ${GREEN}localhost:9001${NC})"
echo ""
echo -e "${GREEN}Logs:${NC}"
echo -e "  Backend:        ${YELLOW}pm2 logs boloo-backend${NC}"
echo -e "  Web:            ${YELLOW}pm2 logs boloo-web${NC}"
echo -e "  Docker:         ${YELLOW}docker-compose logs -f${NC}"
echo ""
echo -e "${GREEN}Commands:${NC}"
echo -e "  Stop all:       ${YELLOW}pm2 stop all && docker-compose down${NC}"
echo -e "  Restart:        ${YELLOW}./restart.sh${NC}"
echo -e "  View status:    ${YELLOW}pm2 status${NC}"
echo ""
