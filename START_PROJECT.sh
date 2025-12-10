#!/bin/bash

###############################################################################
# Boloo App - Emergency Recovery & Startup Script
# Use this if VS Code or Claude Flow crashes
# Usage: ./START_PROJECT.sh
###############################################################################

set -e  # Exit on error

echo "=============================================="
echo "  🚀 Boloo App Recovery & Startup"
echo "=============================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}[1/6] Checking system status...${NC}"

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo -e "${YELLOW}Installing PM2...${NC}"
    npm install -g pm2
fi

# Check if services are already running
if pm2 list | grep -q "boloo-backend"; then
    echo -e "${GREEN}✓ Backend already running${NC}"
    BACKEND_RUNNING=true
else
    BACKEND_RUNNING=false
fi

if pm2 list | grep -q "boloo-mobile"; then
    echo -e "${GREEN}✓ Mobile already running${NC}"
    MOBILE_RUNNING=true
else
    MOBILE_RUNNING=false
fi

echo ""
echo -e "${YELLOW}[2/6] Starting Docker services...${NC}"

# Start Docker services (PostgreSQL, Redis, MinIO)
cd "$SCRIPT_DIR"
docker-compose up -d

# Wait for PostgreSQL
echo -e "${YELLOW}Waiting for PostgreSQL...${NC}"
until docker exec boloo-postgres pg_isready -U postgres > /dev/null 2>&1; do
    sleep 1
done
echo -e "${GREEN}✓ PostgreSQL ready${NC}"

# Wait for Redis
echo -e "${YELLOW}Waiting for Redis...${NC}"
until docker exec boloo-redis redis-cli ping > /dev/null 2>&1; do
    sleep 1
done
echo -e "${GREEN}✓ Redis ready${NC}"

echo ""
echo -e "${YELLOW}[3/6] Checking backend environment...${NC}"

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment and check packages
source venv/bin/activate

# Quick check if critical packages are installed
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}Installing Python dependencies (this may take a few minutes)...${NC}"
    pip install --upgrade pip wheel setuptools
    pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic pydantic python-jose passlib bcrypt python-multipart
    pip install openai anthropic jsonschema azure-ai-formrecognizer redis python-dotenv pyjwt
    pip install "numpy<2" faiss-cpu sentence-transformers scipy
    pip install geoalchemy2 phonenumbers email-validator aiofiles aiosmtplib
    pip install azure-cognitiveservices-speech azure-storage-blob pillow python-magic libmagic
    pip install pydantic-settings uvloop rapidfuzz pydub
fi

echo -e "${GREEN}✓ Backend environment ready${NC}"

echo ""
echo -e "${YELLOW}[4/6] Starting backend server...${NC}"

if [ "$BACKEND_RUNNING" = false ]; then
    cd "$SCRIPT_DIR/backend"
    pm2 start "venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000" --name boloo-backend
    echo -e "${GREEN}✓ Backend started on port 8000${NC}"
else
    pm2 restart boloo-backend
    echo -e "${GREEN}✓ Backend restarted${NC}"
fi

echo ""
echo -e "${YELLOW}[5/6] Starting mobile Expo server...${NC}"

if [ "$MOBILE_RUNNING" = false ]; then
    cd "$SCRIPT_DIR/mobile"
    pm2 start "npx expo start" --name boloo-mobile
    echo -e "${GREEN}✓ Mobile Expo started on port 8081${NC}"
else
    pm2 restart boloo-mobile
    echo -e "${GREEN}✓ Mobile Expo restarted${NC}"
fi

echo ""
echo -e "${YELLOW}[6/6] Saving PM2 configuration...${NC}"
pm2 save

echo ""
echo -e "${GREEN}=============================================="
echo -e "  ✅ All Services Running!"
echo -e "==============================================${NC}"
echo ""
echo -e "${GREEN}Services Status:${NC}"
pm2 status

echo ""
echo -e "${GREEN}Access Points:${NC}"
echo -e "  Backend API:        ${YELLOW}http://localhost:8000${NC}"
echo -e "  API Health:         ${YELLOW}http://localhost:8000/v1/monitoring/health${NC}"
echo -e "  Mobile Expo:        ${YELLOW}http://localhost:8081${NC}"
echo ""
echo -e "${GREEN}Useful Commands:${NC}"
echo -e "  View logs:          ${YELLOW}pm2 logs${NC}"
echo -e "  Backend logs:       ${YELLOW}pm2 logs boloo-backend${NC}"
echo -e "  Mobile logs:        ${YELLOW}pm2 logs boloo-mobile${NC}"
echo -e "  Stop all:           ${YELLOW}pm2 stop all${NC}"
echo -e "  Restart all:        ${YELLOW}pm2 restart all${NC}"
echo -e "  Status:             ${YELLOW}pm2 status${NC}"
echo ""
echo -e "${GREEN}Emergency Recovery:${NC}"
echo -e "  If things break:    ${YELLOW}./START_PROJECT.sh${NC}"
echo -e "  Full reset:         ${YELLOW}./FULL_RESET.sh${NC}"
echo ""

# Wait for backend to fully start
echo -e "${YELLOW}Testing backend connectivity...${NC}"
sleep 10

if curl -s http://localhost:8000/v1/monitoring/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is responding!${NC}"
else
    echo -e "${RED}⚠ Backend may still be starting up. Check: pm2 logs boloo-backend${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Project started successfully!${NC}"
echo -e "${GREEN}Open your mobile app to test the connection.${NC}"
