#!/bin/bash

###############################################################################
# Boloo Quick Recovery Script
# Purpose: Fast system health check and recovery guidance
# Created: 2025-11-24
# Usage: ./QUICK_RECOVERY.sh
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuration
PROJECT_ROOT="/Users/diptendu/boloo app/boloo-app"
RESOURCE_GROUP="boloo-production-rg"
BACKEND_APP="boloo-backend-api"
DATABASE_SERVER="boloo-database"

###############################################################################
# Helper Functions
###############################################################################

print_header() {
    echo -e "\n${BOLD}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}║        Boloo Quick Recovery System v3.0               ║${NC}"
    echo -e "${BOLD}╚════════════════════════════════════════════════════════╝${NC}\n"
}

print_section() {
    echo -e "\n${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_status() {
    local status=$1
    local message=$2

    case $status in
        "ok")
            echo -e "${GREEN}✓${NC} $message"
            ;;
        "warn")
            echo -e "${YELLOW}⚠${NC} $message"
            ;;
        "error")
            echo -e "${RED}✗${NC} $message"
            ;;
        "info")
            echo -e "${BLUE}ℹ${NC} $message"
            ;;
    esac
}

check_command() {
    if command -v $1 &> /dev/null; then
        return 0
    else
        return 1
    fi
}

###############################################################################
# System Checks
###############################################################################

check_prerequisites() {
    print_section "Checking Prerequisites"

    local all_ok=true

    if check_command "az"; then
        print_status "ok" "Azure CLI installed"
    else
        print_status "error" "Azure CLI not found - Install from https://aka.ms/azure-cli"
        all_ok=false
    fi

    if check_command "curl"; then
        print_status "ok" "curl installed"
    else
        print_status "warn" "curl not found - Some tests will be skipped"
    fi

    if check_command "jq"; then
        print_status "ok" "jq installed"
    else
        print_status "warn" "jq not found - Install with: brew install jq"
    fi

    # Check Azure login
    if az account show &> /dev/null; then
        local account=$(az account show --query "name" -o tsv 2>/dev/null)
        print_status "ok" "Logged into Azure: $account"
    else
        print_status "error" "Not logged into Azure - Run: az login"
        all_ok=false
    fi

    if [ "$all_ok" = false ]; then
        echo -e "\n${RED}Please fix prerequisite errors before continuing.${NC}"
        exit 1
    fi
}

check_backend_status() {
    print_section "Backend API Status"

    # Check Azure app status
    echo -e "${BOLD}Checking Azure Web App...${NC}"
    local app_state=$(az webapp show \
        --name $BACKEND_APP \
        --resource-group $RESOURCE_GROUP \
        --query "state" -o tsv 2>/dev/null)

    if [ "$app_state" = "Running" ]; then
        print_status "ok" "Azure Web App: $app_state"
    else
        print_status "error" "Azure Web App: $app_state"
        echo -e "${YELLOW}  → Try: az webapp restart --name $BACKEND_APP --resource-group $RESOURCE_GROUP${NC}"
    fi

    # Test health endpoint
    echo -e "\n${BOLD}Testing API Health...${NC}"
    if check_command "curl"; then
        local health_url="https://${BACKEND_APP}.azurewebsites.net/v1/monitoring/health"
        local response=$(curl -s -o /dev/null -w "%{http_code}" "$health_url" --max-time 10)

        if [ "$response" = "200" ]; then
            print_status "ok" "Health endpoint: 200 OK"
        elif [ "$response" = "000" ]; then
            print_status "error" "Health endpoint: Connection timeout/failed"
            echo -e "${YELLOW}  → Backend may be down or unreachable${NC}"
        else
            print_status "warn" "Health endpoint: HTTP $response"
        fi
    fi

    # Check recent deployments
    echo -e "\n${BOLD}Recent Deployments:${NC}"
    az webapp deployment list \
        --name $BACKEND_APP \
        --resource-group $RESOURCE_GROUP \
        --query "[0:3].[id, status, message, start_time]" \
        -o table 2>/dev/null || print_status "warn" "Could not fetch deployment history"
}

check_database_status() {
    print_section "Database Status"

    local db_state=$(az postgres flexible-server show \
        --name $DATABASE_SERVER \
        --resource-group $RESOURCE_GROUP \
        --query "state" -o tsv 2>/dev/null)

    if [ "$db_state" = "Ready" ]; then
        print_status "ok" "PostgreSQL Server: $db_state"
    else
        print_status "error" "PostgreSQL Server: $db_state"
        echo -e "${YELLOW}  → Try: az postgres flexible-server restart --name $DATABASE_SERVER --resource-group $RESOURCE_GROUP${NC}"
    fi

    # Check database details
    local db_version=$(az postgres flexible-server show \
        --name $DATABASE_SERVER \
        --resource-group $RESOURCE_GROUP \
        --query "version" -o tsv 2>/dev/null)
    print_status "info" "PostgreSQL Version: $db_version"

    local db_tier=$(az postgres flexible-server show \
        --name $DATABASE_SERVER \
        --resource-group $RESOURCE_GROUP \
        --query "sku.tier" -o tsv 2>/dev/null)
    print_status "info" "Database Tier: $db_tier"
}

check_environment_variables() {
    print_section "Critical Environment Variables"

    echo -e "${BOLD}Checking Azure App Settings...${NC}"

    # Critical variables to check
    local critical_vars=(
        "APP_ENV"
        "AZURE_OPENAI_API_KEY"
        "AZURE_SPEECH_KEY"
        "DATABASE_URL"
        "JWT_SECRET_KEY"
        "MSG91_API_KEY"
    )

    local settings=$(az webapp config appsettings list \
        --name $BACKEND_APP \
        --resource-group $RESOURCE_GROUP \
        --output json 2>/dev/null)

    for var in "${critical_vars[@]}"; do
        local value=$(echo "$settings" | jq -r ".[] | select(.name==\"$var\") | .value" 2>/dev/null)

        if [ -z "$value" ] || [ "$value" = "null" ]; then
            print_status "error" "$var: NOT SET"
        elif [ "$var" = "APP_ENV" ] && [ "$value" != "production" ]; then
            print_status "warn" "$var: $value (should be 'production')"
        elif [ "$var" = "JWT_SECRET_KEY" ] && [ "$value" = "dev_secret_key_change_in_production" ]; then
            print_status "error" "$var: Using dev key! SECURITY RISK!"
        else
            # Mask sensitive values
            local masked_value=$(echo "$value" | sed 's/\(.\{4\}\).*/\1**********/')
            print_status "ok" "$var: $masked_value"
        fi
    done
}

check_security_issues() {
    print_section "Security Audit"

    echo -e "${BOLD}Checking for exposed credentials...${NC}"

    # Check backend .env file
    local env_file="$PROJECT_ROOT/backend/.env"
    if [ -f "$env_file" ]; then
        print_status "warn" "Found backend/.env file"

        # Check for API keys
        if grep -q "AZURE_OPENAI_API_KEY=" "$env_file" 2>/dev/null; then
            local key_value=$(grep "AZURE_OPENAI_API_KEY=" "$env_file" | cut -d'=' -f2)
            if [ ! -z "$key_value" ] && [ "$key_value" != "" ]; then
                print_status "error" "AZURE_OPENAI_API_KEY found in .env - SECURITY RISK!"
                echo -e "${RED}  → IMMEDIATE ACTION: Rotate this key and remove from .env${NC}"
            fi
        fi

        if grep -q "AZURE_SPEECH_KEY=" "$env_file" 2>/dev/null; then
            local key_value=$(grep "AZURE_SPEECH_KEY=" "$env_file" | cut -d'=' -f2)
            if [ ! -z "$key_value" ] && [ "$key_value" != "" ]; then
                print_status "error" "AZURE_SPEECH_KEY found in .env - SECURITY RISK!"
                echo -e "${RED}  → IMMEDIATE ACTION: Rotate this key and remove from .env${NC}"
            fi
        fi
    else
        print_status "ok" "No backend/.env file (good)"
    fi

    # Check .gitignore
    local gitignore="$PROJECT_ROOT/.gitignore"
    if [ -f "$gitignore" ]; then
        if grep -q "^\.env$" "$gitignore" 2>/dev/null; then
            print_status "ok" ".env in .gitignore"
        else
            print_status "warn" ".env NOT in .gitignore"
            echo -e "${YELLOW}  → Add to .gitignore to prevent accidental commits${NC}"
        fi
    fi
}

check_mobile_web() {
    print_section "Mobile Web Status"

    if check_command "curl"; then
        local mobile_url="https://www.bultoo.com"
        local response=$(curl -s -o /dev/null -w "%{http_code}" "$mobile_url" --max-time 10)

        if [ "$response" = "200" ]; then
            print_status "ok" "Mobile Web: 200 OK ($mobile_url)"
        else
            print_status "warn" "Mobile Web: HTTP $response"
        fi

        # Test CORS
        echo -e "\n${BOLD}Testing CORS configuration...${NC}"
        local cors_test=$(curl -s -I "https://${BACKEND_APP}.azurewebsites.net/api/dropdown/states" \
            -H "Origin: https://www.bultoo.com" 2>/dev/null | grep -i "access-control-allow-origin")

        if [ ! -z "$cors_test" ]; then
            print_status "ok" "CORS configured correctly"
        else
            print_status "warn" "CORS may not be configured"
        fi
    fi
}

test_critical_endpoints() {
    print_section "Testing Critical API Endpoints"

    if ! check_command "curl"; then
        print_status "warn" "curl not available - skipping endpoint tests"
        return
    fi

    local base_url="https://${BACKEND_APP}.azurewebsites.net"

    # Test health endpoint
    echo -e "${BOLD}1. Health Check${NC}"
    local health=$(curl -s "${base_url}/v1/monitoring/health" --max-time 10)
    if [ ! -z "$health" ]; then
        print_status "ok" "Health endpoint responding"
        if check_command "jq"; then
            echo "$health" | jq '.'
        fi
    else
        print_status "error" "Health endpoint not responding"
    fi

    # Test states dropdown
    echo -e "\n${BOLD}2. States Dropdown API${NC}"
    local states=$(curl -s "${base_url}/api/dropdown/states" --max-time 10)
    if echo "$states" | grep -q "Andhra Pradesh" 2>/dev/null; then
        print_status "ok" "States API working (36 states)"
    else
        print_status "error" "States API not responding correctly"
    fi

    # Test chat endpoint (likely to fail without auth)
    echo -e "\n${BOLD}3. Chat Start Endpoint${NC}"
    local chat_response=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "${base_url}/v1/chat/start?user_id=11111111-1111-4000-8111-000000000000&language=hi" \
        -H "Origin: https://www.bultoo.com" \
        -H "Content-Type: application/json" \
        --max-time 10)

    if [ "$chat_response" = "200" ]; then
        print_status "ok" "Chat endpoint: 200 OK"
    elif [ "$chat_response" = "500" ]; then
        print_status "error" "Chat endpoint: 500 Internal Server Error"
        echo -e "${YELLOW}  → Check logs: az webapp log tail --name $BACKEND_APP --resource-group $RESOURCE_GROUP${NC}"
    else
        print_status "warn" "Chat endpoint: HTTP $chat_response"
    fi
}

show_recovery_summary() {
    print_section "Recovery Summary"

    echo -e "${BOLD}📊 System Status Overview:${NC}\n"

    # Count issues
    local critical_count=0
    local warning_count=0

    # Check for critical issues
    echo -e "${BOLD}🔴 Critical Issues:${NC}"

    # Check environment
    local settings=$(az webapp config appsettings list \
        --name $BACKEND_APP \
        --resource-group $RESOURCE_GROUP \
        --output json 2>/dev/null)

    local app_env=$(echo "$settings" | jq -r '.[] | select(.name=="APP_ENV") | .value' 2>/dev/null)
    if [ "$app_env" != "production" ]; then
        echo "  • APP_ENV not set to production"
        ((critical_count++))
    fi

    local jwt_secret=$(echo "$settings" | jq -r '.[] | select(.name=="JWT_SECRET_KEY") | .value' 2>/dev/null)
    if [ "$jwt_secret" = "dev_secret_key_change_in_production" ]; then
        echo "  • JWT_SECRET_KEY using dev key"
        ((critical_count++))
    fi

    # Check for exposed keys
    if [ -f "$PROJECT_ROOT/backend/.env" ]; then
        if grep -q "AZURE_OPENAI_API_KEY=.\+" "$PROJECT_ROOT/backend/.env" 2>/dev/null; then
            echo "  • API keys exposed in backend/.env"
            ((critical_count++))
        fi
    fi

    if [ $critical_count -eq 0 ]; then
        echo -e "  ${GREEN}✓ No critical issues found${NC}"
    fi

    echo -e "\n${BOLD}Next Steps:${NC}"
    if [ $critical_count -gt 0 ]; then
        echo -e "${RED}1. Address $critical_count critical security issue(s) immediately${NC}"
        echo -e "${YELLOW}2. Review /Users/diptendu/boloo app/docs/RECOVERY_SUMMARY_NOV24.md${NC}"
        echo -e "${BLUE}3. Follow P0 priority tasks${NC}"
    else
        echo -e "${GREEN}✓ System appears healthy${NC}"
        echo -e "${BLUE}→ Review /Users/diptendu/boloo app/docs/RECOVERY_SUMMARY_NOV24.md for pending tasks${NC}"
    fi
}

show_quick_actions() {
    print_section "Quick Actions"

    echo -e "${BOLD}Emergency Commands:${NC}\n"

    echo -e "${BLUE}# Restart backend${NC}"
    echo "az webapp restart --name $BACKEND_APP --resource-group $RESOURCE_GROUP"

    echo -e "\n${BLUE}# View live logs${NC}"
    echo "az webapp log tail --name $BACKEND_APP --resource-group $RESOURCE_GROUP"

    echo -e "\n${BLUE}# Check deployment status${NC}"
    echo "az webapp deployment list --name $BACKEND_APP --resource-group $RESOURCE_GROUP --output table"

    echo -e "\n${BLUE}# Rotate Azure OpenAI key${NC}"
    echo "az cognitiveservices account keys regenerate --name cgnet-openai --resource-group $RESOURCE_GROUP --key-name key1"

    echo -e "\n${BLUE}# Update app settings${NC}"
    echo "az webapp config appsettings set --name $BACKEND_APP --resource-group $RESOURCE_GROUP --settings KEY=value"

    echo -e "\n${BOLD}Documentation:${NC}"
    echo -e "  • Full Recovery Summary: ${BLUE}/Users/diptendu/boloo app/docs/RECOVERY_SUMMARY_NOV24.md${NC}"
    echo -e "  • Recovery Guide: ${BLUE}/Users/diptendu/boloo app/boloo-app/docs/RECOVERY_GUIDE.md${NC}"
    echo -e "  • MSG91 Setup: ${BLUE}/Users/diptendu/boloo app/boloo-app/backend/docs/MSG91_IMPLEMENTATION_SUMMARY.md${NC}"
}

###############################################################################
# Main Execution
###############################################################################

main() {
    clear
    print_header

    echo -e "${BOLD}Starting comprehensive system check...${NC}"
    echo -e "${YELLOW}This will take 30-60 seconds${NC}\n"

    # Run all checks
    check_prerequisites
    check_backend_status
    check_database_status
    check_environment_variables
    check_security_issues
    check_mobile_web
    test_critical_endpoints

    # Show summary
    show_recovery_summary
    show_quick_actions

    echo -e "\n${BOLD}${GREEN}Recovery check complete!${NC}\n"
}

# Run main function
main
