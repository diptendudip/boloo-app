#!/bin/bash

# Monitoring System Test Script
# Tests all monitoring endpoints and verifies functionality

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URL
API_URL="http://localhost:8000"

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Boloo Monitoring System Test Suite${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Function to test an endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local expected_status="$4"

    echo -n "Testing: $name... "

    response=$(curl -s -w "\n%{http_code}" -X "$method" "${API_URL}${endpoint}")
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)

    if [ "$http_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_status, got $http_code)"
        echo -e "${YELLOW}Response: $body${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Function to test JSON response
test_json_field() {
    local name="$1"
    local endpoint="$2"
    local field="$3"

    echo -n "Testing: $name... "

    response=$(curl -s "${API_URL}${endpoint}")
    value=$(echo "$response" | jq -r "$field" 2>/dev/null)

    if [ -n "$value" ] && [ "$value" != "null" ]; then
        echo -e "${GREEN}✓ PASS${NC} (Value: $value)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Field not found or null)"
        echo -e "${YELLOW}Response: $response${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo -e "${BLUE}[1/10] Basic Health Check${NC}"
test_endpoint "Basic health endpoint" "GET" "/health" 200
echo ""

echo -e "${BLUE}[2/10] API Documentation${NC}"
test_endpoint "API docs available" "GET" "/docs" 200
echo ""

echo -e "${BLUE}[3/10] Trigger Health Check${NC}"
test_endpoint "Manual health check trigger" "POST" "/v1/monitoring/health/check" 200
echo "Waiting 3 seconds for health check to complete..."
sleep 3
echo ""

echo -e "${BLUE}[4/10] Health Dashboard${NC}"
test_endpoint "Get health dashboard" "GET" "/v1/monitoring/health/dashboard" 200
test_json_field "Dashboard has timestamp" "/v1/monitoring/health/dashboard" ".timestamp"
test_json_field "Dashboard has overall health" "/v1/monitoring/health/dashboard" ".overall_health.total_resources"
echo ""

echo -e "${BLUE}[5/10] Health Summary${NC}"
test_endpoint "Get health summary" "GET" "/v1/monitoring/health/summary" 200
test_json_field "Summary has status" "/v1/monitoring/health/summary" ".status"
test_json_field "Summary has health score" "/v1/monitoring/health/summary" ".health_score"
echo ""

echo -e "${BLUE}[6/10] Resources List${NC}"
test_endpoint "Get all resources" "GET" "/v1/monitoring/health/resources" 200
test_json_field "Resources list has count" "/v1/monitoring/health/resources" ".count"
echo ""

echo -e "${BLUE}[7/10] Filter Internal Resources${NC}"
test_endpoint "Get internal resources only" "GET" "/v1/monitoring/health/resources?resource_type=internal" 200
echo ""

echo -e "${BLUE}[8/10] Filter by Status${NC}"
test_endpoint "Get healthy resources (status=2)" "GET" "/v1/monitoring/health/resources?status=2" 200
echo ""

echo -e "${BLUE}[9/10] Alerts${NC}"
test_endpoint "Get health alerts" "GET" "/v1/monitoring/health/alerts" 200
test_json_field "Alerts has total count" "/v1/monitoring/health/alerts" ".total_alerts"
echo ""

echo -e "${BLUE}[10/10] Resource Details${NC}"
# URL encode resource name
test_endpoint "Get PostgreSQL details" "GET" "/v1/monitoring/health/resources/PostgreSQL%20Database" 200
echo ""

# Summary
echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Test Results Summary${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "Total Tests: $((TESTS_PASSED + TESTS_FAILED))"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. View dashboard: curl http://localhost:8000/v1/monitoring/health/dashboard | jq"
    echo "  2. View API docs: http://localhost:8000/docs"
    echo "  3. Check database: docker exec -it boloo-postgres psql -U boloo -d boloo"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some tests failed. Please check the output above.${NC}"
    exit 1
fi
