#!/bin/bash

###############################################################################
# Boloo First Run Setup Script
# Simpler version for first-time setup
###############################################################################

set -e

echo "======================================================"
echo "  Boloo First-Time Setup"
echo "======================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check Docker
echo -e "${YELLOW}[1/8] Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Docker is not running!${NC}"
    echo -e "${YELLOW}Please start Docker Desktop and try again.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Start Docker services
echo -e "${YELLOW}[2/8] Starting Docker services...${NC}"
docker-compose up -d postgres redis minio
echo -e "${GREEN}✓ Docker services started${NC}"
echo ""

# Wait for PostgreSQL
echo -e "${YELLOW}[3/8] Waiting for PostgreSQL...${NC}"
sleep 10
until docker-compose exec -T postgres pg_isready -U boloo &> /dev/null; do
    echo -e "${YELLOW}Still waiting for PostgreSQL...${NC}"
    sleep 3
done
echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
echo ""

# Setup backend
echo -e "${YELLOW}[4/8] Setting up backend...${NC}"
cd backend

# Create Python virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate and install dependencies
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Backend dependencies installed${NC}"
echo ""

# Create database tables
echo -e "${YELLOW}[5/8] Creating database tables...${NC}"
python3 << 'PYEOF'
from app.database import engine, Base
from app.models import *
print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("✓ Tables created")
PYEOF
echo ""

# Load seed data (only if psql is available)
echo -e "${YELLOW}[6/8] Loading seed data...${NC}"
cd ..
if command -v psql &> /dev/null; then
    psql postgresql://boloo:boloo_dev_password@localhost:5432/boloo < database/seeds/01_taxonomies.sql 2>/dev/null || echo "Taxonomies already loaded or error occurred"
    psql postgresql://boloo:boloo_dev_password@localhost:5432/boloo < database/seeds/02_entities.sql 2>/dev/null || echo "Entities already loaded or error occurred"
    echo -e "${GREEN}✓ Seed data loaded${NC}"
else
    echo -e "${YELLOW}⚠ psql not found, skipping seed data (will auto-create on first API call)${NC}"
fi
echo ""

# Start backend with PM2
echo -e "${YELLOW}[7/8] Starting backend server (daemon mode)...${NC}"
cd backend
source venv/bin/activate
pm2 delete boloo-backend 2>/dev/null || true
pm2 start "venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000" --name boloo-backend --interpreter none
pm2 save
echo -e "${GREEN}✓ Backend started on port 8000${NC}"
cd ..

# Start web with PM2
echo -e "${YELLOW}[8/8] Starting web console (daemon mode)...${NC}"
cd web

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing web dependencies (this may take 2-3 minutes)...${NC}"
    npm install
fi

# Create .env file
if [ ! -f ".env.local" ]; then
    echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
fi

pm2 delete boloo-web 2>/dev/null || true
pm2 start npm --name boloo-web -- run dev
pm2 save
echo -e "${GREEN}✓ Web console started on port 3000${NC}"
cd ..

echo ""
echo -e "${GREEN}======================================================"
echo -e "  ✓ Setup Complete!"
echo -e "======================================================${NC}"
echo ""
echo -e "${GREEN}Access your application:${NC}"
echo -e "  Web Admin:    ${GREEN}http://localhost:3000${NC}"
echo -e "  Monitoring:   ${GREEN}http://localhost:3000/monitoring${NC}"
echo -e "  Backend API:  ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs:     ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${GREEN}Check status:${NC}"
echo -e "  ${YELLOW}pm2 status${NC}"
echo -e "  ${YELLOW}docker-compose ps${NC}"
echo ""
echo -e "${GREEN}View logs:${NC}"
echo -e "  ${YELLOW}pm2 logs boloo-backend${NC}"
echo -e "  ${YELLOW}pm2 logs boloo-web${NC}"
echo ""
