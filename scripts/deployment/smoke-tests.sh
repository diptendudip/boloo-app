#!/bin/bash
# Deployment Smoke Tests
# Quick validation tests for critical user flows
# Author: DevOps Team
# Version: 1.0.0

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BACKEND_URL="${BACKEND_URL:-https://boloo-backend-api.azurewebsites.net}"
FRONTEND_URL="${FRONTEND_URL:-https://www.bultoo.com}"
TEST_USER_ID="11111111-1111-4000-8111-000000000000"
TIMEOUT=10

# Test results
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

log() {
    echo -e "${2:-$NC}[$(date +'%H:%M:%S')] $1${NC}"
}

log_test() {
    echo -e "${BLUE}[TEST] $1${NC}"
}

log_success() {
    echo -e "${GREEN}  ✅ PASS: $1${NC}"
    ((TESTS_PASSED++))
}

log_failure() {
    echo -e "${RED}  ❌ FAIL: $1${NC}"
    ((TESTS_FAILED++))
}

run_test() {
    ((TESTS_RUN++))
}

# Test 1: Health Check
test_health_check() {
    run_test
    log_test "Health Check Endpoint"

    local response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT "$BACKEND_URL/health" 2>&1 || echo -e "\n000")
    local http_code=$(echo "$response" | tail -n 1)

    if [ "$http_code" == "200" ]; then
        log_success "Health endpoint returns 200 OK"
        return 0
    else
        log_failure "Health endpoint returned HTTP $http_code"
        return 1
    fi
}

# Test 2: Chat Start Endpoint
test_chat_start() {
    run_test
    log_test "Chat Start Endpoint (/v1/chat/start)"

    local response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
        -X POST "$BACKEND_URL/v1/chat/start?user_id=$TEST_USER_ID&language=hi" \
        -H "Origin: $FRONTEND_URL" \
        -H "Content-Type: application/json" \
        2>&1 || echo -e "\n000")

    local body=$(echo "$response" | head -n -1)
    local http_code=$(echo "$response" | tail -n 1)

    if [ "$http_code" == "200" ]; then
        log_success "Chat start endpoint returns 200 OK"

        # Validate response structure
        if command -v jq &> /dev/null; then
            if echo "$body" | jq -e '.conversation_id' &> /dev/null; then
                log_success "Response contains conversation_id"
            else
                log_failure "Response missing conversation_id"
                return 1
            fi

            if echo "$body" | jq -e '.message' &> /dev/null; then
                log_success "Response contains message"
            else
                log_failure "Response missing message"
                return 1
            fi
        fi

        return 0
    else
        log_failure "Chat start returned HTTP $http_code"
        echo "    Response: $(echo "$body" | head -c 200)"
        return 1
    fi
}

# Test 3: States Dropdown Endpoint
test_states_dropdown() {
    run_test
    log_test "States Dropdown Endpoint (/api/dropdown/states)"

    local response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
        -H "Origin: $FRONTEND_URL" \
        "$BACKEND_URL/api/dropdown/states" \
        2>&1 || echo -e "\n000")

    local body=$(echo "$response" | head -n -1)
    local http_code=$(echo "$response" | tail -n 1)

    if [ "$http_code" == "200" ]; then
        log_success "States endpoint returns 200 OK"

        # Validate data
        if command -v jq &> /dev/null; then
            local count=$(echo "$body" | jq '. | length' 2>/dev/null || echo "0")
            if [ "$count" -gt 0 ]; then
                log_success "Returned $count states"
            else
                log_failure "No states data returned"
                return 1
            fi
        fi

        return 0
    else
        log_failure "States endpoint returned HTTP $http_code"
        return 1
    fi
}

# Test 4: Districts Dropdown Endpoint
test_districts_dropdown() {
    run_test
    log_test "Districts Dropdown Endpoint (/api/dropdown/districts)"

    local response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
        -H "Origin: $FRONTEND_URL" \
        "$BACKEND_URL/api/dropdown/districts?stateCode=MH" \
        2>&1 || echo -e "\n000")

    local body=$(echo "$response" | head -n -1)
    local http_code=$(echo "$response" | tail -n 1)

    if [ "$http_code" == "200" ]; then
        log_success "Districts endpoint returns 200 OK"

        if command -v jq &> /dev/null; then
            local count=$(echo "$body" | jq '. | length' 2>/dev/null || echo "0")
            if [ "$count" -gt 0 ]; then
                log_success "Returned $count districts for Maharashtra"
            else
                log_failure "No districts data returned"
                return 1
            fi
        fi

        return 0
    else
        log_failure "Districts endpoint returned HTTP $http_code"
        return 1
    fi
}

# Test 5: CORS Headers
test_cors_headers() {
    run_test
    log_test "CORS Headers Validation"

    local response=$(curl -s -I -X OPTIONS \
        -H "Origin: $FRONTEND_URL" \
        -H "Access-Control-Request-Method: POST" \
        -H "Access-Control-Request-Headers: Content-Type" \
        "$BACKEND_URL/v1/chat/start" 2>&1)

    local cors_origin=$(echo "$response" | grep -i "access-control-allow-origin" || echo "")
    local cors_methods=$(echo "$response" | grep -i "access-control-allow-methods" || echo "")
    local cors_headers=$(echo "$response" | grep -i "access-control-allow-headers" || echo "")

    if [ -n "$cors_origin" ]; then
        log_success "CORS Allow-Origin header present"
    else
        log_failure "CORS Allow-Origin header missing"
        return 1
    fi

    if [ -n "$cors_methods" ]; then
        log_success "CORS Allow-Methods header present"
    else
        log_failure "CORS Allow-Methods header missing"
        return 1
    fi

    if [ -n "$cors_headers" ]; then
        log_success "CORS Allow-Headers header present"
    else
        log_failure "CORS Allow-Headers header missing"
        return 1
    fi

    return 0
}

# Test 6: Database Connectivity
test_database_connectivity() {
    run_test
    log_test "Database Connectivity"

    # Database is tested implicitly through states endpoint
    local response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
        "$BACKEND_URL/api/dropdown/states" \
        2>&1 || echo -e "\n000")

    local http_code=$(echo "$response" | tail -n 1)

    if [ "$http_code" == "200" ]; then
        log_success "Database query successful"
        return 0
    else
        log_failure "Database query failed (HTTP $http_code)"
        return 1
    fi
}

# Test 7: API Documentation
test_api_docs() {
    run_test
    log_test "API Documentation Availability"

    local response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
        "$BACKEND_URL/api/v1/docs" \
        2>&1 || echo -e "\n000")

    local http_code=$(echo "$response" | tail -n 1)

    if [ "$http_code" == "200" ]; then
        log_success "API documentation accessible"
        return 0
    else
        log_failure "API documentation not accessible (HTTP $http_code)"
        return 1
    fi
}

# Test 8: Frontend Availability
test_frontend_availability() {
    run_test
    log_test "Frontend Availability"

    local response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
        "$FRONTEND_URL" \
        2>&1 || echo -e "\n000")

    local http_code=$(echo "$response" | tail -n 1)

    if [ "$http_code" == "200" ]; then
        log_success "Frontend accessible"
        return 0
    else
        log_failure "Frontend not accessible (HTTP $http_code)"
        return 1
    fi
}

# Test 9: Response Time Check
test_response_times() {
    run_test
    log_test "Response Time Performance"

    local endpoint="/api/dropdown/states"
    local max_time=2000  # 2 seconds max

    local start_time=$(date +%s%3N)
    local http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
        "$BACKEND_URL$endpoint" || echo "000")
    local end_time=$(date +%s%3N)
    local response_time=$((end_time - start_time))

    if [[ "$http_code" =~ ^[23] ]] && [ $response_time -lt $max_time ]; then
        log_success "Response time ${response_time}ms (under ${max_time}ms threshold)"
        return 0
    elif [ $response_time -ge $max_time ]; then
        log_failure "Response time ${response_time}ms exceeds ${max_time}ms threshold"
        return 1
    else
        log_failure "Request failed with HTTP $http_code"
        return 1
    fi
}

# Test 10: End-to-End User Flow
test_e2e_user_flow() {
    run_test
    log_test "End-to-End User Flow Simulation"

    # Step 1: Get states
    local states_response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
        -H "Origin: $FRONTEND_URL" \
        "$BACKEND_URL/api/dropdown/states" || echo -e "\n000")

    local states_code=$(echo "$states_response" | tail -n 1)

    if [ "$states_code" != "200" ]; then
        log_failure "Step 1 (Get States) failed: HTTP $states_code"
        return 1
    fi

    # Step 2: Get districts
    local districts_response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
        -H "Origin: $FRONTEND_URL" \
        "$BACKEND_URL/api/dropdown/districts?stateCode=MH" || echo -e "\n000")

    local districts_code=$(echo "$districts_response" | tail -n 1)

    if [ "$districts_code" != "200" ]; then
        log_failure "Step 2 (Get Districts) failed: HTTP $districts_code"
        return 1
    fi

    # Step 3: Start chat
    local chat_response=$(curl -s -w "\n%{http_code}" --max-time $TIMEOUT \
        -X POST "$BACKEND_URL/v1/chat/start?user_id=$TEST_USER_ID&language=hi" \
        -H "Origin: $FRONTEND_URL" \
        -H "Content-Type: application/json" \
        || echo -e "\n000")

    local chat_code=$(echo "$chat_response" | tail -n 1)

    if [ "$chat_code" != "200" ]; then
        log_failure "Step 3 (Start Chat) failed: HTTP $chat_code"
        return 1
    fi

    log_success "Complete user flow executed successfully"
    return 0
}

# Main execution
main() {
    echo ""
    log "═══════════════════════════════════════════════════════════" "$BLUE"
    log "  SMOKE TESTS - Boloo Deployment" "$BLUE"
    log "═══════════════════════════════════════════════════════════" "$BLUE"
    log "Backend: $BACKEND_URL" "$BLUE"
    log "Frontend: $FRONTEND_URL" "$BLUE"
    log "Test User ID: $TEST_USER_ID" "$BLUE"
    log "═══════════════════════════════════════════════════════════" "$BLUE"
    echo ""

    # Run all tests
    test_health_check
    test_chat_start
    test_states_dropdown
    test_districts_dropdown
    test_cors_headers
    test_database_connectivity
    test_api_docs
    test_frontend_availability
    test_response_times
    test_e2e_user_flow

    # Summary
    echo ""
    log "═══════════════════════════════════════════════════════════" "$BLUE"
    log "  TEST RESULTS" "$BLUE"
    log "═══════════════════════════════════════════════════════════" "$BLUE"
    log "Tests Run: $TESTS_RUN" "$BLUE"
    log "Tests Passed: $TESTS_PASSED" "$GREEN"
    log "Tests Failed: $TESTS_FAILED" "$RED"

    local pass_rate=0
    if [ $TESTS_RUN -gt 0 ]; then
        pass_rate=$(awk "BEGIN {printf \"%.1f\", ($TESTS_PASSED/$TESTS_RUN)*100}")
    fi
    log "Pass Rate: ${pass_rate}%" "$BLUE"
    log "═══════════════════════════════════════════════════════════" "$BLUE"
    echo ""

    # Exit with appropriate code
    if [ $TESTS_FAILED -eq 0 ]; then
        log "✅ ALL SMOKE TESTS PASSED" "$GREEN"
        exit 0
    else
        log "❌ SOME SMOKE TESTS FAILED" "$RED"
        exit 1
    fi
}

# Run main
main "$@"
