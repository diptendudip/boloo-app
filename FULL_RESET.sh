#!/bin/bash

###############################################################################
# Boloo App - FULL RESET Script (Nuclear Option)
# WARNING: This will delete ALL local data and rebuild from scratch
# Use this ONLY when START_PROJECT.sh fails
# Usage: ./FULL_RESET.sh
###############################################################################

set -e  # Exit on error

echo "=============================================="
echo "  ⚠️  FULL SYSTEM RESET - NUCLEAR OPTION"
echo "=============================================="
echo ""
echo "This will:"
echo "  1. Stop all PM2 processes"
echo "  2. Delete Python virtual environment"
echo "  3. Rebuild all Docker containers"
echo "  4. Reinstall all dependencies"
echo "  5. Reset database (data loss!)"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Confirmation prompt
read -p "$(echo -e ${RED}Are you sure? This will delete ALL data! [yes/no]:${NC} )" -r
echo
if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "Reset cancelled."
    exit 1
fi

echo -e "${RED}[1/8] Stopping all PM2 processes...${NC}"
pm2 kill || true
echo -e "${GREEN}✓ PM2 processes stopped${NC}"

echo ""
echo -e "${RED}[2/8] Stopping and removing Docker containers...${NC}"
docker-compose down -v || true
echo -e "${GREEN}✓ Docker containers removed${NC}"

echo ""
echo -e "${RED}[3/8] Removing Python virtual environment...${NC}"
cd backend
rm -rf venv __pycache__ .pytest_cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}✓ Python environment cleaned${NC}"

echo ""
echo -e "${YELLOW}[4/8] Creating fresh Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip wheel setuptools
echo -e "${GREEN}✓ Virtual environment created${NC}"

echo ""
echo -e "${YELLOW}[5/8] Installing Python dependencies (this will take several minutes)...${NC}"
pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic pydantic python-jose passlib bcrypt python-multipart
pip install openai anthropic jsonschema azure-ai-formrecognizer redis python-dotenv pyjwt
pip install "numpy<2" faiss-cpu sentence-transformers scipy
pip install geoalchemy2 phonenumbers email-validator aiofiles aiosmtplib
pip install azure-cognitiveservices-speech azure-storage-blob pillow python-magic libmagic
pip install pydantic-settings uvloop rapidfuzz pydub
echo -e "${GREEN}✓ All dependencies installed${NC}"

echo ""
echo -e "${YELLOW}[6/8] Starting Docker services...${NC}"
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
echo -e "${YELLOW}[7/8] Running database migrations...${NC}"
cd backend
source venv/bin/activate
alembic upgrade head || echo -e "${YELLOW}Warning: Migration may have failed. Check manually.${NC}"
echo -e "${GREEN}✓ Database migrations attempted${NC}"

echo ""
echo -e "${YELLOW}[8/8] Starting services with PM2...${NC}"
cd "$SCRIPT_DIR/backend"
pm2 start "venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000" --name boloo-backend

cd "$SCRIPT_DIR/mobile"
pm2 start "npx expo start" --name boloo-mobile

pm2 save

echo ""
echo -e "${GREEN}==============================================${NC}"
echo -e "${GREEN}  ✅ Full Reset Complete!${NC}"
echo -e "${GREEN}==============================================${NC}"
echo ""
echo -e "${GREEN}Services Status:${NC}"
pm2 status

echo ""
echo -e "${YELLOW}Testing backend connectivity...${NC}"
sleep 10

if curl -s http://localhost:8000/v1/monitoring/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is responding!${NC}"
else
    echo -e "${RED}⚠ Backend may still be starting. Check: pm2 logs boloo-backend${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Full reset completed successfully!${NC}"
echo -e "${YELLOW}Note: All local data has been reset to initial state.${NC}"
