#!/bin/bash
# Deployment Validation Script
# Validates Azure App Service deployment health and functionality
# Author: DevOps Team
# Version: 1.0.0

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${BACKEND_URL:-https://boloo-backend-api.azurewebsites.net}"
FRONTEND_URL="${FRONTEND_URL:-https://www.bultoo.com}"
RESOURCE_GROUP="${RESOURCE_GROUP:-boloo-production-rg}"
BACKEND_APP_NAME="${BACKEND_APP_NAME:-boloo-backend-api}"
FRONTEND_APP_NAME="${FRONTEND_APP_NAME:-www.bultoo.com}"

# Thresholds
MAX_ERROR_RATE=0.05  # 5% error rate threshold
MAX_RESPONSE_TIME=2000  # 2 seconds max response time (ms)
MIN_SUCCESS_RATE=0.95  # 95% success rate required
VALIDATION_TIMEOUT=300  # 5 minutes total timeout

# Logging
LOG_FILE="/tmp/deployment-validation-$(date +%Y%m%d-%H%M%S).log"
METRICS_FILE="/tmp/deployment-metrics-$(date +%Y%m%d-%H%M%S).json"

log() {
    echo -e "${2:-$NC}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    log "✅ $1" "$GREEN"
}

log_error() {
    log "❌ $1" "$RED"
}

log_warning() {
    log "⚠️  $1" "$YELLOW"
}

# Check if Azure CLI is installed
check_prerequisites() {
    log "Checking prerequisites..."

    if ! command -v az &> /dev/null; then
        log_error "Azure CLI not found. Please install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        exit 1
    fi

    if ! command -v curl &> /dev/null; then
        log_error "curl not found. Please install curl."
        exit 1
    fi

    if ! command -v jq &> /dev/null; then
        log_warning "jq not found. JSON parsing will be limited."
    fi

    log_success "Prerequisites check passed"
}

# Check Azure authentication
check_azure_auth() {
    log "Checking Azure authentication..."

    if ! az account show &> /dev/null; then
        log_error "Not authenticated to Azure. Run: az login"
        exit 1
    fi

    local subscription=$(az account show --query name -o tsv)
    log_success "Authenticated to Azure subscription: $subscription"
}

# Check backend app status
check_backend_status() {
    log "Checking backend app service status..."

    local state=$(az webapp show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$BACKEND_APP_NAME" \
        --query state -o tsv 2>/dev/null || echo "NOT_FOUND")

    if [ "$state" != "Running" ]; then
        log_error "Backend app is not running. Current state: $state"
        return 1
    fi

    log_success "Backend app service is running"
    return 0
}

# Test health endpoint
test_health_endpoint() {
    log "Testing health endpoint..."

    local response=$(curl -s -w "\n%{http_code}" --max-time 10 "$BACKEND_URL/health" || echo -e "\n000")
    local body=$(echo "$response" | head -n -1)
    local http_code=$(echo "$response" | tail -n 1)

    if [ "$http_code" != "200" ]; then
        log_error "Health check failed with HTTP $http_code"
        log_error "Response: $body"
        return 1
    fi

    log_success "Health endpoint responding (HTTP 200)"

    # Parse health check details if available
    if command -v jq &> /dev/null && echo "$body" | jq -e . &> /dev/null; then
        local db_status=$(echo "$body" | jq -r '.database // "unknown"')
        local redis_status=$(echo "$body" | jq -r '.redis // "unknown"')

        if [ "$db_status" == "healthy" ]; then
            log_success "Database connection: healthy"
        else
            log_warning "Database status: $db_status"
        fi

        if [ "$redis_status" == "healthy" ]; then
            log_success "Redis connection: healthy"
        fi
    fi

    return 0
}

# Test critical API endpoints
test_critical_endpoints() {
    log "Testing critical API endpoints..."

    local endpoints=(
        "/v1/chat/start?user_id=11111111-1111-4000-8111-000000000000&language=hi POST"
        "/api/dropdown/states GET"
        "/api/dropdown/districts?stateCode=MH GET"
        "/api/v1/docs GET"
    )

    local failed_count=0
    local total_response_time=0
    local success_count=0

    for endpoint_info in "${endpoints[@]}"; do
        local endpoint=$(echo "$endpoint_info" | awk '{print $1}')
        local method=$(echo "$endpoint_info" | awk '{print $2}')
        local url="$BACKEND_URL$endpoint"

        log "Testing $method $endpoint..."

        # Measure response time
        local start_time=$(date +%s%3N)
        local response=$(curl -s -w "\n%{http_code}" --max-time 10 \
            -X "$method" \
            -H "Origin: $FRONTEND_URL" \
            -H "Content-Type: application/json" \
            "$url" 2>&1 || echo -e "\n000")
        local end_time=$(date +%s%3N)
        local response_time=$((end_time - start_time))

        local http_code=$(echo "$response" | tail -n 1)
        local body=$(echo "$response" | head -n -1)

        total_response_time=$((total_response_time + response_time))

        if [[ "$http_code" =~ ^[23] ]]; then
            log_success "  ✓ HTTP $http_code - ${response_time}ms"
            ((success_count++))

            if [ $response_time -gt $MAX_RESPONSE_TIME ]; then
                log_warning "  Response time ${response_time}ms exceeds threshold ${MAX_RESPONSE_TIME}ms"
            fi
        else
            log_error "  ✗ HTTP $http_code - ${response_time}ms"
            log_error "  Response: $(echo "$body" | head -c 200)"
            ((failed_count++))
        fi
    done

    local total_tests=${#endpoints[@]}
    local success_rate=$(awk "BEGIN {printf \"%.2f\", $success_count/$total_tests}")
    local avg_response_time=$((total_response_time / total_tests))

    log "Endpoint test summary: $success_count/$total_tests passed (${success_rate})"
    log "Average response time: ${avg_response_time}ms"

    if (( $(echo "$success_rate < $MIN_SUCCESS_RATE" | bc -l) )); then
        log_error "Success rate ${success_rate} below threshold ${MIN_SUCCESS_RATE}"
        return 1
    fi

    log_success "Critical endpoints validation passed"
    return 0
}

# Test CORS headers
test_cors_headers() {
    log "Testing CORS headers..."

    local response=$(curl -s -I -X OPTIONS \
        -H "Origin: $FRONTEND_URL" \
        -H "Access-Control-Request-Method: POST" \
        "$BACKEND_URL/v1/chat/start" 2>&1)

    if echo "$response" | grep -qi "access-control-allow-origin"; then
        log_success "CORS headers present"

        if echo "$response" | grep -qi "access-control-allow-origin: \*\|$FRONTEND_URL"; then
            log_success "CORS origin correctly configured"
        else
            log_warning "CORS origin might not match frontend URL"
        fi

        return 0
    else
        log_error "CORS headers missing"
        return 1
    fi
}

# Check database connectivity
check_database_connectivity() {
    log "Checking database connectivity..."

    # Test through API endpoint that requires DB
    local response=$(curl -s -w "\n%{http_code}" --max-time 10 \
        "$BACKEND_URL/api/dropdown/states" || echo -e "\n000")
    local http_code=$(echo "$response" | tail -n 1)
    local body=$(echo "$response" | head -n -1)

    if [ "$http_code" == "200" ]; then
        # Check if we got actual data
        if command -v jq &> /dev/null && echo "$body" | jq -e '. | length > 0' &> /dev/null; then
            local count=$(echo "$body" | jq '. | length')
            log_success "Database connectivity verified ($count states returned)"
            return 0
        elif echo "$body" | grep -q "state"; then
            log_success "Database connectivity verified"
            return 0
        fi
    fi

    log_error "Database connectivity test failed"
    return 1
}

# Check error rates in recent logs
check_error_rates() {
    log "Checking error rates in recent logs..."

    # Get last 100 log entries
    local logs=$(az webapp log download \
        --resource-group "$RESOURCE_GROUP" \
        --name "$BACKEND_APP_NAME" \
        --log-file "/tmp/app-logs.zip" 2>&1 || true)

    if [ -f "/tmp/app-logs.zip" ]; then
        log "Analyzing recent application logs..."

        # Extract and analyze (simplified)
        unzip -q -o "/tmp/app-logs.zip" -d "/tmp/app-logs" 2>/dev/null || true

        if [ -d "/tmp/app-logs" ]; then
            local error_count=$(grep -ri "error\|exception\|critical" /tmp/app-logs 2>/dev/null | wc -l)
            local total_count=$(find /tmp/app-logs -type f -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')

            if [ "$total_count" -gt 0 ]; then
                local error_rate=$(awk "BEGIN {printf \"%.4f\", $error_count/$total_count}")
                log "Error rate: ${error_rate} ($error_count errors in $total_count log lines)"

                if (( $(echo "$error_rate > $MAX_ERROR_RATE" | bc -l) )); then
                    log_error "Error rate ${error_rate} exceeds threshold ${MAX_ERROR_RATE}"
                    rm -rf /tmp/app-logs /tmp/app-logs.zip
                    return 1
                fi
            fi

            rm -rf /tmp/app-logs /tmp/app-logs.zip
        fi

        log_success "Error rate is within acceptable limits"
    else
        log_warning "Could not download logs for analysis"
    fi

    return 0
}

# Check response times
check_response_times() {
    log "Checking response times..."

    local test_endpoint="/api/dropdown/states"
    local iterations=5
    local total_time=0
    local failed=0

    for i in $(seq 1 $iterations); do
        local start_time=$(date +%s%3N)
        local http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
            "$BACKEND_URL$test_endpoint" || echo "000")
        local end_time=$(date +%s%3N)
        local response_time=$((end_time - start_time))

        if [[ ! "$http_code" =~ ^[23] ]]; then
            ((failed++))
            continue
        fi

        total_time=$((total_time + response_time))
        log "  Iteration $i: ${response_time}ms"
    done

    local successful=$((iterations - failed))
    if [ $successful -gt 0 ]; then
        local avg_time=$((total_time / successful))
        log "Average response time: ${avg_time}ms (${successful}/${iterations} successful)"

        if [ $avg_time -gt $MAX_RESPONSE_TIME ]; then
            log_warning "Average response time ${avg_time}ms exceeds threshold ${MAX_RESPONSE_TIME}ms"
        else
            log_success "Response times are acceptable"
        fi
    else
        log_error "All response time tests failed"
        return 1
    fi

    return 0
}

# Verify environment configuration
verify_environment_config() {
    log "Verifying environment configuration..."

    local app_settings=$(az webapp config appsettings list \
        --resource-group "$RESOURCE_GROUP" \
        --name "$BACKEND_APP_NAME" -o json 2>/dev/null)

    if [ -z "$app_settings" ]; then
        log_error "Could not retrieve app settings"
        return 1
    fi

    # Check critical environment variables
    local critical_vars=(
        "DATABASE_URL"
        "AZURE_OPENAI_ENDPOINT"
        "AZURE_OPENAI_API_KEY"
        "JWT_SECRET_KEY"
    )

    local missing_vars=0
    for var in "${critical_vars[@]}"; do
        if echo "$app_settings" | grep -q "\"name\": \"$var\""; then
            log_success "  ✓ $var configured"
        else
            log_error "  ✗ $var missing"
            ((missing_vars++))
        fi
    done

    if [ $missing_vars -gt 0 ]; then
        log_error "$missing_vars critical environment variables missing"
        return 1
    fi

    log_success "Environment configuration verified"
    return 0
}

# Generate metrics report
generate_metrics_report() {
    log "Generating metrics report..."

    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    cat > "$METRICS_FILE" <<EOF
{
  "timestamp": "$timestamp",
  "deployment_validation": {
    "backend_url": "$BACKEND_URL",
    "frontend_url": "$FRONTEND_URL",
    "validation_status": "completed",
    "log_file": "$LOG_FILE"
  },
  "checks_performed": [
    "prerequisites",
    "azure_authentication",
    "backend_status",
    "health_endpoint",
    "critical_endpoints",
    "cors_headers",
    "database_connectivity",
    "error_rates",
    "response_times",
    "environment_config"
  ]
}
EOF

    log_success "Metrics report saved to: $METRICS_FILE"
}

# Main validation flow
main() {
    log "═══════════════════════════════════════════════════════════"
    log "  DEPLOYMENT VALIDATION - Boloo Backend API"
    log "═══════════════════════════════════════════════════════════"
    log "Backend: $BACKEND_URL"
    log "Frontend: $FRONTEND_URL"
    log "Resource Group: $RESOURCE_GROUP"
    log "═══════════════════════════════════════════════════════════"

    local validation_failed=0

    # Run all validation checks
    check_prerequisites || ((validation_failed++))
    check_azure_auth || ((validation_failed++))
    check_backend_status || ((validation_failed++))
    test_health_endpoint || ((validation_failed++))
    test_critical_endpoints || ((validation_failed++))
    test_cors_headers || ((validation_failed++))
    check_database_connectivity || ((validation_failed++))
    verify_environment_config || ((validation_failed++))
    check_error_rates || ((validation_failed++))
    check_response_times || ((validation_failed++))

    # Generate report
    generate_metrics_report

    log "═══════════════════════════════════════════════════════════"
    if [ $validation_failed -eq 0 ]; then
        log_success "VALIDATION PASSED - Deployment is healthy"
        log "Log file: $LOG_FILE"
        log "Metrics file: $METRICS_FILE"
        log "═══════════════════════════════════════════════════════════"
        exit 0
    else
        log_error "VALIDATION FAILED - $validation_failed check(s) failed"
        log "Log file: $LOG_FILE"
        log "Metrics file: $METRICS_FILE"
        log "═══════════════════════════════════════════════════════════"
        exit 1
    fi
}

# Run main function
main "$@"
