#!/bin/bash

# Deployment Testing Script
# Usage: ./scripts/test-deployment.sh [base-url]
# Example: ./scripts/test-deployment.sh https://boloo-backend-api.azurewebsites.net

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="${1:-https://boloo-backend-api.azurewebsites.net}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Boloo Backend Deployment Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Testing:${NC} $BASE_URL"
echo ""

print_test() {
    echo -e "${BLUE}Testing:${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

TESTS_PASSED=0
TESTS_FAILED=0

# Test 1: Health endpoint
print_test "Health endpoint (/health)"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/health" || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    print_success "Health endpoint returned 200"
    echo "Response: $BODY"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_error "Health endpoint failed with code $HTTP_CODE"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 2: API documentation
print_test "API documentation (/docs)"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/docs")

if [ "$HTTP_CODE" = "200" ]; then
    print_success "API docs accessible"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_error "API docs failed with code $HTTP_CODE"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 3: OpenAPI schema
print_test "OpenAPI schema (/openapi.json)"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/openapi.json")

if [ "$HTTP_CODE" = "200" ]; then
    print_success "OpenAPI schema accessible"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_error "OpenAPI schema failed with code $HTTP_CODE"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 4: CORS headers
print_test "CORS headers"
CORS_HEADERS=$(curl -s -I -X OPTIONS "$BASE_URL/health" | grep -i "access-control-allow")

if [ -n "$CORS_HEADERS" ]; then
    print_success "CORS headers present"
    echo "$CORS_HEADERS"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_error "CORS headers missing"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 5: Response time
print_test "Response time"
START_TIME=$(date +%s%N)
curl -s "$BASE_URL/health" > /dev/null
END_TIME=$(date +%s%N)
RESPONSE_TIME=$(( (END_TIME - START_TIME) / 1000000 ))

if [ $RESPONSE_TIME -lt 2000 ]; then
    print_success "Response time: ${RESPONSE_TIME}ms (< 2s)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
elif [ $RESPONSE_TIME -lt 5000 ]; then
    echo -e "${YELLOW}⚠ Response time: ${RESPONSE_TIME}ms (2-5s)${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_error "Response time: ${RESPONSE_TIME}ms (> 5s)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 6: Security headers
print_test "Security headers"
SECURITY_HEADERS=$(curl -s -I "$BASE_URL/health" | grep -iE "(x-frame-options|x-content-type-options|strict-transport-security)")

if [ -n "$SECURITY_HEADERS" ]; then
    print_success "Security headers present"
    echo "$SECURITY_HEADERS"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}⚠ Some security headers may be missing${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi
echo ""

# Test 7: JSON response validation
print_test "JSON response validation"
JSON_RESPONSE=$(curl -s "$BASE_URL/health")

if echo "$JSON_RESPONSE" | jq . > /dev/null 2>&1; then
    print_success "Valid JSON response"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_error "Invalid JSON response"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Test 8: 404 handling
print_test "404 error handling"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/nonexistent-endpoint")

if [ "$HTTP_CODE" = "404" ]; then
    print_success "404 handled correctly"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    print_error "404 not handled correctly (got $HTTP_CODE)"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi
echo ""

# Summary
TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
SUCCESS_RATE=$(( (TESTS_PASSED * 100) / TOTAL_TESTS ))

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Total tests:${NC} $TOTAL_TESTS"
echo -e "${GREEN}Passed:${NC} $TESTS_PASSED"
echo -e "${RED}Failed:${NC} $TESTS_FAILED"
echo -e "${YELLOW}Success rate:${NC} $SUCCESS_RATE%"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed! ✗${NC}"
    exit 1
fi
