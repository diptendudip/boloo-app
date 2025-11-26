#!/bin/bash

# Complete Test Suite Runner for Authentication & Persistence
# This script runs all test suites and generates a comprehensive report

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
BACKEND_EXIT=0
MOBILE_EXIT=0
DOCKER_EXIT=0
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}🧪 AUTHENTICATION & PERSISTENCE TEST SUITE${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}📋 Checking Prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 installed${NC}"

# Check pytest
if ! python3 -m pytest --version &> /dev/null; then
    echo -e "${YELLOW}⚠️  pytest not found. Installing...${NC}"
    pip install pytest pytest-cov pytest-html requests
fi
echo -e "${GREEN}✓ pytest installed${NC}"

# Check if backend is running
echo -e "\n${YELLOW}🔍 Checking if backend server is running...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend server is running${NC}"
else
    echo -e "${RED}❌ Backend server is not running on http://localhost:8000${NC}"
    echo -e "${YELLOW}Please start the backend server:${NC}"
    echo -e "${YELLOW}   uvicorn app.main:app --reload --port 8000${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}📦 TEST SUITE 1: Backend API Tests${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

pytest tests/test_auth_persistence.py -v --tb=short --color=yes || BACKEND_EXIT=$?

if [ $BACKEND_EXIT -eq 0 ]; then
    echo -e "\n${GREEN}✅ Backend API Tests: PASSED${NC}\n"
else
    echo -e "\n${RED}❌ Backend API Tests: FAILED${NC}\n"
fi

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}📱 TEST SUITE 2: Mobile Integration Tests${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

pytest tests/integration/test_mobile_auth_flow.py -v -s --tb=short --color=yes || MOBILE_EXIT=$?

if [ $MOBILE_EXIT -eq 0 ]; then
    echo -e "\n${GREEN}✅ Mobile Integration Tests: PASSED${NC}\n"
else
    echo -e "\n${RED}❌ Mobile Integration Tests: FAILED${NC}\n"
fi

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}🐳 TEST SUITE 3: Docker Smoke Tests${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Check if we should run Docker tests
if [ "$1" == "--skip-docker" ]; then
    echo -e "${YELLOW}⏭️  Skipping Docker tests (--skip-docker flag)${NC}"
    DOCKER_EXIT=0
else
    pytest tests/smoke/test_docker_deployment.py -v -s --tb=short --color=yes || DOCKER_EXIT=$?

    if [ $DOCKER_EXIT -eq 0 ]; then
        echo -e "\n${GREEN}✅ Docker Smoke Tests: PASSED${NC}\n"
    else
        echo -e "\n${RED}❌ Docker Smoke Tests: FAILED${NC}\n"
    fi
fi

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}📊 TEST SUITE SUMMARY${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Calculate totals
TOTAL_FAILED=$((BACKEND_EXIT + MOBILE_EXIT + DOCKER_EXIT))

# Print summary
if [ $BACKEND_EXIT -eq 0 ]; then
    echo -e "${GREEN}✅ Backend API Tests: PASSED${NC}"
else
    echo -e "${RED}❌ Backend API Tests: FAILED${NC}"
fi

if [ $MOBILE_EXIT -eq 0 ]; then
    echo -e "${GREEN}✅ Mobile Integration Tests: PASSED${NC}"
else
    echo -e "${RED}❌ Mobile Integration Tests: FAILED${NC}"
fi

if [ "$1" != "--skip-docker" ]; then
    if [ $DOCKER_EXIT -eq 0 ]; then
        echo -e "${GREEN}✅ Docker Smoke Tests: PASSED${NC}"
    else
        echo -e "${RED}❌ Docker Smoke Tests: FAILED${NC}"
    fi
fi

echo ""
echo -e "${BLUE}============================================================${NC}"

if [ $TOTAL_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED${NC}"
    echo -e "${GREEN}✅ System is ready for production${NC}"
    echo -e "${BLUE}============================================================${NC}"
    exit 0
else
    echo -e "${RED}⚠️  SOME TESTS FAILED${NC}"
    echo -e "${RED}❌ Please fix failing tests before deployment${NC}"
    echo -e "${BLUE}============================================================${NC}"
    exit 1
fi
