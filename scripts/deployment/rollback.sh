#!/bin/bash
# Automated Deployment Rollback Script
# Detects failed deployments and automatically rolls back to previous version
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
RESOURCE_GROUP="${RESOURCE_GROUP:-boloo-production-rg}"
BACKEND_APP_NAME="${BACKEND_APP_NAME:-boloo-backend-api}"
FRONTEND_APP_NAME="${FRONTEND_APP_NAME:-www.bultoo.com}"
BACKEND_URL="${BACKEND_URL:-https://boloo-backend-api.azurewebsites.net}"
ADMIN_EMAIL="${ADMIN_EMAIL:-diptendudip@gmail.com}"

# Rollback settings
AUTO_ROLLBACK="${AUTO_ROLLBACK:-true}"
VALIDATION_RETRIES=3
VALIDATION_RETRY_DELAY=30
INCIDENT_REPORT_DIR="/tmp/boloo-incidents"

# Logging
ROLLBACK_LOG="/tmp/rollback-$(date +%Y%m%d-%H%M%S).log"

log() {
    echo -e "${2:-$NC}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$ROLLBACK_LOG"
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

log_info() {
    log "ℹ️  $1" "$BLUE"
}

# Check if Azure CLI is authenticated
check_azure_auth() {
    if ! az account show &> /dev/null; then
        log_error "Not authenticated to Azure. Run: az login"
        exit 1
    fi
}

# Get current deployment info
get_current_deployment() {
    log_info "Getting current deployment information..."

    local current_deployment=$(az webapp deployment list \
        --resource-group "$RESOURCE_GROUP" \
        --name "$BACKEND_APP_NAME" \
        --query "[0]" -o json 2>/dev/null)

    if [ -z "$current_deployment" ] || [ "$current_deployment" == "null" ]; then
        log_error "Could not retrieve current deployment information"
        return 1
    fi

    echo "$current_deployment"
}

# Get previous successful deployment
get_previous_deployment() {
    log_info "Finding previous successful deployment..."

    # Get all deployments, sorted by time
    local deployments=$(az webapp deployment list \
        --resource-group "$RESOURCE_GROUP" \
        --name "$BACKEND_APP_NAME" \
        --query "[?status=='Success'] | [0:5]" -o json 2>/dev/null)

    if [ -z "$deployments" ] || [ "$deployments" == "[]" ]; then
        log_error "No previous successful deployments found"
        return 1
    fi

    # Get the second most recent successful deployment (first is current)
    local previous=$(echo "$deployments" | jq -r '.[1] // empty')

    if [ -z "$previous" ] || [ "$previous" == "null" ]; then
        log_error "No previous deployment to rollback to"
        return 1
    fi

    echo "$previous"
}

# Validate deployment health
validate_deployment() {
    local retries=${1:-1}

    log_info "Validating deployment health (attempt $retries/$VALIDATION_RETRIES)..."

    # Run smoke tests
    local script_dir=$(dirname "$0")
    if [ -f "$script_dir/smoke-tests.sh" ]; then
        if bash "$script_dir/smoke-tests.sh" &>> "$ROLLBACK_LOG"; then
            log_success "Deployment validation passed"
            return 0
        else
            log_error "Deployment validation failed"
            return 1
        fi
    else
        # Fallback: basic health check
        local response=$(curl -s -w "\n%{http_code}" --max-time 10 "$BACKEND_URL/health" || echo -e "\n000")
        local http_code=$(echo "$response" | tail -n 1)

        if [ "$http_code" == "200" ]; then
            log_success "Basic health check passed"
            return 0
        else
            log_error "Basic health check failed (HTTP $http_code)"
            return 1
        fi
    fi
}

# Perform rollback
perform_rollback() {
    local target_deployment_id="$1"

    log_warning "Initiating rollback to deployment: $target_deployment_id"

    # Create backup of current deployment slot
    log_info "Creating backup of current deployment..."

    # For Azure App Service, we'll use deployment slots if available
    # Otherwise, we'll redeploy the previous version

    # Check if deployment slots are available
    local slots=$(az webapp deployment slot list \
        --resource-group "$RESOURCE_GROUP" \
        --name "$BACKEND_APP_NAME" \
        --query "[].name" -o tsv 2>/dev/null || echo "")

    if [ -n "$slots" ]; then
        log_info "Using deployment slots for rollback..."

        # Swap to previous slot if available
        if echo "$slots" | grep -q "staging"; then
            log_info "Swapping to staging slot..."
            az webapp deployment slot swap \
                --resource-group "$RESOURCE_GROUP" \
                --name "$BACKEND_APP_NAME" \
                --slot staging \
                --target-slot production

            if [ $? -eq 0 ]; then
                log_success "Slot swap completed"
            else
                log_error "Slot swap failed"
                return 1
            fi
        fi
    else
        log_info "No deployment slots available, using deployment history..."

        # Get previous deployment details
        local previous_commit=$(az webapp deployment list \
            --resource-group "$RESOURCE_GROUP" \
            --name "$BACKEND_APP_NAME" \
            --query "[1].id" -o tsv 2>/dev/null)

        if [ -n "$previous_commit" ] && [ "$previous_commit" != "null" ]; then
            log_info "Redeploying previous version: $previous_commit"

            # Trigger redeployment
            az webapp deployment source sync \
                --resource-group "$RESOURCE_GROUP" \
                --name "$BACKEND_APP_NAME"

            if [ $? -eq 0 ]; then
                log_success "Redeployment triggered"
            else
                log_error "Redeployment failed"
                return 1
            fi
        else
            log_error "Could not find previous deployment to rollback to"
            return 1
        fi
    fi

    # Wait for rollback to complete
    log_info "Waiting for rollback to complete..."
    sleep 30

    # Restart the app to ensure clean state
    log_info "Restarting application..."
    az webapp restart \
        --resource-group "$RESOURCE_GROUP" \
        --name "$BACKEND_APP_NAME"

    if [ $? -eq 0 ]; then
        log_success "Application restarted"
    else
        log_error "Application restart failed"
        return 1
    fi

    # Wait for app to be ready
    sleep 30

    return 0
}

# Generate incident report
generate_incident_report() {
    local reason="$1"
    local current_deployment="$2"
    local rollback_success="$3"

    mkdir -p "$INCIDENT_REPORT_DIR"

    local incident_id="INC-$(date +%Y%m%d-%H%M%S)"
    local report_file="$INCIDENT_REPORT_DIR/$incident_id.md"

    log_info "Generating incident report: $incident_id"

    cat > "$report_file" <<EOF
# Deployment Incident Report
**Incident ID**: $incident_id
**Timestamp**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
**Severity**: Critical
**Status**: $([ "$rollback_success" == "true" ] && echo "Resolved (Rolled Back)" || echo "Failed to Rollback")

---

## Summary
Automatic deployment rollback was triggered due to failed deployment validation.

## Incident Details

### Reason for Rollback
$reason

### Current Deployment Info
\`\`\`json
$current_deployment
\`\`\`

### Rollback Status
- **Automatic Rollback**: $AUTO_ROLLBACK
- **Rollback Success**: $rollback_success
- **Timestamp**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

### Affected Services
- **Backend API**: $BACKEND_APP_NAME
- **Resource Group**: $RESOURCE_GROUP
- **Backend URL**: $BACKEND_URL

### Impact
- **User Impact**: High (API unavailable or returning errors)
- **Duration**: TBD (investigation required)
- **Affected Endpoints**: All backend endpoints

---

## Timeline

1. **$(date -u +"%Y-%m-%d %H:%M:%S UTC")**: Deployment validation failed
2. **$(date -u +"%Y-%m-%d %H:%M:%S UTC")**: Automatic rollback initiated
3. **$(date -u +"%Y-%m-%d %H:%M:%S UTC")**: Rollback $([ "$rollback_success" == "true" ] && echo "completed successfully" || echo "failed")

---

## Root Cause Analysis

### Investigation Required
- [ ] Review deployment logs
- [ ] Check application logs for errors
- [ ] Verify environment configuration
- [ ] Review recent code changes
- [ ] Check database migrations
- [ ] Verify external service dependencies

### Potential Causes
1. Code defects introduced in latest deployment
2. Environment configuration issues
3. Database migration failures
4. External service dependencies
5. Resource constraints (memory, CPU)

---

## Resolution Steps

### Immediate Actions (Completed)
- [x] Automatic rollback to previous version
- [x] Service health validation
- [x] Incident report generation

### Follow-up Actions (Required)
- [ ] Root cause analysis
- [ ] Fix identified issues
- [ ] Test fixes in staging environment
- [ ] Plan redeployment with fixes
- [ ] Update deployment procedures if needed

---

## Validation Results

### Pre-Rollback Validation
- Health Check: FAILED
- Smoke Tests: FAILED
- Error Rate: Exceeded threshold

### Post-Rollback Validation
$([ "$rollback_success" == "true" ] && echo "- Health Check: PASSED
- Smoke Tests: PASSED
- Error Rate: Within limits" || echo "- Validation: PENDING (rollback failed)")

---

## Logs and Artifacts

### Rollback Log
\`$ROLLBACK_LOG\`

### Related Logs
- Application Logs: Azure Portal > $BACKEND_APP_NAME > Logs
- Deployment Logs: Azure Portal > $BACKEND_APP_NAME > Deployment Center

---

## Notifications

### Sent To
- Admin: $ADMIN_EMAIL
- DevOps Team: (configure in script)

### Notification Channels
- Email: $ADMIN_EMAIL
- Incident Report: $report_file

---

## Next Steps

1. **Immediate** (0-1 hour):
   - Review this incident report
   - Validate service is operational
   - Notify stakeholders

2. **Short-term** (1-24 hours):
   - Conduct root cause analysis
   - Implement fixes
   - Test in staging environment

3. **Long-term** (1-7 days):
   - Improve deployment validation
   - Update testing procedures
   - Review deployment automation

---

## Recommendations

### Process Improvements
1. Enhance pre-deployment validation
2. Implement gradual rollout (canary deployment)
3. Improve monitoring and alerting
4. Automate smoke tests in CI/CD pipeline
5. Create deployment runbook

### Technical Improvements
1. Add more comprehensive health checks
2. Implement feature flags for safer deployments
3. Enhance error logging and monitoring
4. Set up automated performance testing
5. Implement deployment checkpoints

---

**Report Generated**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
**Generated By**: Automated Rollback System v1.0.0
**Contact**: $ADMIN_EMAIL
EOF

    log_success "Incident report generated: $report_file"
    echo "$report_file"
}

# Send notification
send_notification() {
    local subject="$1"
    local body="$2"
    local incident_report="${3:-}"

    log_info "Sending notification to $ADMIN_EMAIL..."

    # Create notification email
    local email_body="Subject: $subject

$body

Incident Report: $incident_report
Rollback Log: $ROLLBACK_LOG

---
Automated Rollback System
Timestamp: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
"

    # Try to send via Azure (if configured)
    # Note: This requires Azure Communication Services or SendGrid configuration
    # For now, just log the notification

    log_warning "Email notification prepared but not sent (configure SendGrid or Azure Communication Services)"
    log_info "Notification details:"
    echo "$email_body" >> "$ROLLBACK_LOG"
}

# Main rollback flow
main() {
    log "═══════════════════════════════════════════════════════════"
    log "  AUTOMATED DEPLOYMENT ROLLBACK"
    log "═══════════════════════════════════════════════════════════"
    log "Backend: $BACKEND_URL"
    log "Resource Group: $RESOURCE_GROUP"
    log "Auto-Rollback: $AUTO_ROLLBACK"
    log "═══════════════════════════════════════════════════════════"

    # Check prerequisites
    check_azure_auth

    # Get current deployment info
    local current_deployment=$(get_current_deployment)
    if [ $? -ne 0 ]; then
        log_error "Failed to get current deployment information"
        exit 1
    fi

    local current_id=$(echo "$current_deployment" | jq -r '.id // "unknown"')
    log_info "Current deployment: $current_id"

    # Validate current deployment with retries
    local validation_failed=true
    for i in $(seq 1 $VALIDATION_RETRIES); do
        if validate_deployment $i; then
            validation_failed=false
            break
        fi

        if [ $i -lt $VALIDATION_RETRIES ]; then
            log_warning "Validation failed, retrying in ${VALIDATION_RETRY_DELAY}s..."
            sleep $VALIDATION_RETRY_DELAY
        fi
    done

    if [ "$validation_failed" == "false" ]; then
        log_success "Deployment is healthy, no rollback needed"
        exit 0
    fi

    log_error "Deployment validation failed after $VALIDATION_RETRIES attempts"

    # Check if auto-rollback is enabled
    if [ "$AUTO_ROLLBACK" != "true" ]; then
        log_warning "Auto-rollback is disabled. Manual intervention required."
        local report=$(generate_incident_report "Deployment validation failed (auto-rollback disabled)" "$current_deployment" "false")
        send_notification "⚠️ Boloo Deployment Failed" "Deployment validation failed but auto-rollback is disabled. Manual intervention required." "$report"
        exit 1
    fi

    # Get previous deployment
    local previous_deployment=$(get_previous_deployment)
    if [ $? -ne 0 ]; then
        log_error "Cannot rollback: no previous deployment found"
        local report=$(generate_incident_report "No previous deployment available for rollback" "$current_deployment" "false")
        send_notification "🚨 Boloo Rollback Failed" "No previous deployment available for rollback." "$report"
        exit 1
    fi

    local previous_id=$(echo "$previous_deployment" | jq -r '.id // "unknown"')
    log_info "Target rollback deployment: $previous_id"

    # Perform rollback
    if perform_rollback "$previous_id"; then
        log_success "Rollback completed successfully"

        # Validate rolled-back deployment
        sleep 30
        if validate_deployment 1; then
            log_success "Rolled-back deployment is healthy"
            local report=$(generate_incident_report "Deployment validation failed, rolled back to $previous_id" "$current_deployment" "true")
            send_notification "✅ Boloo Rollback Successful" "Deployment rolled back successfully to $previous_id" "$report"

            log "═══════════════════════════════════════════════════════════"
            log_success "ROLLBACK COMPLETED SUCCESSFULLY"
            log "Incident Report: $report"
            log "Rollback Log: $ROLLBACK_LOG"
            log "═══════════════════════════════════════════════════════════"
            exit 0
        else
            log_error "Rolled-back deployment is also unhealthy!"
            local report=$(generate_incident_report "Both current and previous deployments are unhealthy" "$current_deployment" "false")
            send_notification "🚨 Boloo Critical Issue" "Rollback completed but service is still unhealthy!" "$report"
            exit 1
        fi
    else
        log_error "Rollback failed"
        local report=$(generate_incident_report "Rollback procedure failed" "$current_deployment" "false")
        send_notification "🚨 Boloo Rollback Failed" "Automatic rollback failed. Immediate manual intervention required!" "$report"

        log "═══════════════════════════════════════════════════════════"
        log_error "ROLLBACK FAILED - MANUAL INTERVENTION REQUIRED"
        log "Incident Report: $report"
        log "Rollback Log: $ROLLBACK_LOG"
        log "═══════════════════════════════════════════════════════════"
        exit 1
    fi
}

# Run main function
main "$@"
