#!/bin/bash
# Work Recovery Detection Script
# Purpose: Analyze recent work and suggest next steps after crash
# Created: 2025-11-22

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

CHECKPOINT_DIR=".recovery/checkpoints"

echo -e "${BOLD}${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║     Boloo Crash Recovery System v2.0      ║${NC}"
echo -e "${BOLD}${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# 1. Find latest checkpoint
echo -e "${YELLOW}📂 Checking for saved checkpoints...${NC}"
LATEST_CHECKPOINT=$(ls -1t "$CHECKPOINT_DIR"/checkpoint_*.json 2>/dev/null | head -1)

if [ -n "$LATEST_CHECKPOINT" ]; then
    echo -e "${GREEN}✓ Found checkpoint: $(basename "$LATEST_CHECKPOINT")${NC}"
    echo ""
    echo -e "${BOLD}Last Checkpoint Summary:${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Parse checkpoint data
    CHECKPOINT_TIME=$(jq -r '.local_time' "$LATEST_CHECKPOINT")
    BRANCH=$(jq -r '.git.branch' "$LATEST_CHECKPOINT")
    CHANGES=$(jq -r '.git.uncommitted_changes' "$LATEST_CHECKPOINT")

    echo -e "  ${YELLOW}Time:${NC}     $CHECKPOINT_TIME"
    echo -e "  ${YELLOW}Branch:${NC}   $BRANCH"
    echo -e "  ${YELLOW}Changes:${NC}  $CHANGES uncommitted files"
    echo ""

    # Show recent commits
    echo -e "${BOLD}Recent Commits:${NC}"
    jq -r '.git.recent_commits[]' "$LATEST_CHECKPOINT" 2>/dev/null | sed 's/^/  ✓ /'
    echo ""

    # Show recently modified files
    echo -e "${BOLD}Recently Modified Files:${NC}"
    jq -r '.recent_files_modified[]' "$LATEST_CHECKPOINT" 2>/dev/null | sed 's/^/  📝 /'
    echo ""
else
    echo -e "${YELLOW}⚠️  No checkpoints found${NC}"
    echo ""
fi

# 2. Analyze current state
echo -e "${YELLOW}🔍 Analyzing current system state...${NC}"
echo ""

# Check services
echo -e "${BOLD}Service Status:${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# PM2
if command -v pm2 &> /dev/null; then
    PM2_COUNT=$(pm2 jlist 2>/dev/null | jq '. | length' 2>/dev/null || echo 0)
    if [ "$PM2_COUNT" -gt 0 ]; then
        echo -e "  ${GREEN}✓ PM2:${NC}     $PM2_COUNT processes running"
        pm2 jlist 2>/dev/null | jq -r '.[] | "    - \(.name): \(.pm2_env.status)"' 2>/dev/null || true
    else
        echo -e "  ${RED}✗ PM2:${NC}     No processes running"
    fi
else
    echo -e "  ${YELLOW}⚠ PM2:${NC}     Not installed"
fi

# Docker
if command -v docker &> /dev/null; then
    DOCKER_COUNT=$(docker ps -q 2>/dev/null | wc -l | tr -d ' ')
    if [ "$DOCKER_COUNT" -gt 0 ]; then
        echo -e "  ${GREEN}✓ Docker:${NC}  $DOCKER_COUNT containers running"
        docker ps --format "    - {{.Names}}: {{.Status}}" 2>/dev/null | head -5
    else
        echo -e "  ${RED}✗ Docker:${NC}  No containers running"
    fi
else
    echo -e "  ${YELLOW}⚠ Docker:${NC}  Not installed"
fi

echo ""

# 3. Analyze recent file changes
echo -e "${BOLD}Recent File Activity (Last Hour):${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

RECENT_PY=$(find . -name "*.py" -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/venv/*" -mmin -60 2>/dev/null | wc -l | tr -d ' ')
RECENT_TS=$(find . \( -name "*.ts" -o -name "*.tsx" \) -not -path "*/node_modules/*" -not -path "*/.git/*" -mmin -60 2>/dev/null | wc -l | tr -d ' ')
RECENT_MD=$(find . -name "*.md" -not -path "*/node_modules/*" -not -path "*/.git/*" -mmin -60 2>/dev/null | wc -l | tr -d ' ')

echo -e "  📄 Python files:     $RECENT_PY modified"
echo -e "  📄 TypeScript files: $RECENT_TS modified"
echo -e "  📄 Markdown files:   $RECENT_MD modified"

if [ "$RECENT_PY" -gt 0 ] || [ "$RECENT_TS" -gt 0 ] || [ "$RECENT_MD" -gt 0 ]; then
    echo ""
    echo -e "  ${BOLD}Top 5 Recent Files:${NC}"
    find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.md" \) \
        -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/venv/*" \
        -mmin -60 -exec ls -lt {} + 2>/dev/null | head -6 | tail -5 | \
        awk '{print "    - " $9}' || true
fi

echo ""

# 4. Check git status
if [ -d .git ]; then
    echo -e "${BOLD}Git Status:${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
    UNTRACKED=$(git status --short 2>/dev/null | grep "^??" | wc -l | tr -d ' ')
    MODIFIED=$(git status --short 2>/dev/null | grep "^ M" | wc -l | tr -d ' ')
    STAGED=$(git status --short 2>/dev/null | grep "^M" | wc -l | tr -d ' ')

    echo -e "  ${YELLOW}Branch:${NC}     $BRANCH"
    echo -e "  ${YELLOW}Untracked:${NC}  $UNTRACKED files"
    echo -e "  ${YELLOW}Modified:${NC}   $MODIFIED files"
    echo -e "  ${YELLOW}Staged:${NC}     $STAGED files"

    if [ "$UNTRACKED" -gt 0 ] || [ "$MODIFIED" -gt 0 ]; then
        echo ""
        echo -e "  ${BOLD}Recent Changes:${NC}"
        git status --short 2>/dev/null | head -10 | sed 's/^/    /'
    fi

    echo ""
fi

# 5. Suggest next steps
echo -e "${BOLD}${GREEN}💡 Suggested Next Steps:${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Determine what was being worked on
CONTEXT="general"
if [ "$RECENT_PY" -gt "$RECENT_TS" ]; then
    CONTEXT="backend"
elif [ "$RECENT_TS" -gt "$RECENT_PY" ]; then
    CONTEXT="frontend"
elif [ "$RECENT_MD" -gt 0 ]; then
    CONTEXT="documentation"
fi

case $CONTEXT in
    backend)
        echo -e "  ${YELLOW}Detected:${NC} Backend Python development"
        echo ""
        echo "  1. Check backend logs:"
        echo "     ${BLUE}pm2 logs boloo-backend${NC}"
        echo ""
        echo "  2. Restart backend if needed:"
        echo "     ${BLUE}pm2 restart boloo-backend${NC}"
        echo ""
        echo "  3. Continue backend work:"
        echo "     ${BLUE}cd backend && source venv/bin/activate${NC}"
        ;;
    frontend)
        echo -e "  ${YELLOW}Detected:${NC} Frontend TypeScript development"
        echo ""
        echo "  1. Check mobile/web logs:"
        echo "     ${BLUE}pm2 logs boloo-mobile${NC}"
        echo ""
        echo "  2. Restart development server:"
        echo "     ${BLUE}cd mobile && npx expo start${NC}"
        echo "     ${BLUE}cd web && npm run dev${NC}"
        ;;
    documentation)
        echo -e "  ${YELLOW}Detected:${NC} Documentation work"
        echo ""
        echo "  1. Review recent documentation:"
        echo "     ${BLUE}ls -lt docs/*.md | head -5${NC}"
        echo ""
        echo "  2. Continue documentation:"
        echo "     ${BLUE}cd docs${NC}"
        ;;
    *)
        echo -e "  ${YELLOW}General recovery steps:${NC}"
        echo ""
        echo "  1. Check all services:"
        echo "     ${BLUE}pm2 status && docker ps${NC}"
        echo ""
        echo "  2. Review git changes:"
        echo "     ${BLUE}git status${NC}"
        echo ""
        echo "  3. Check recent files:"
        echo "     ${BLUE}ls -lt | head -10${NC}"
        ;;
esac

echo ""
echo -e "  ${BOLD}Always Available:${NC}"
echo "  • Start services:  ${BLUE}./START_PROJECT.sh${NC}"
echo "  • Full reset:      ${BLUE}./FULL_RESET.sh${NC} (destructive)"
echo "  • Azure recovery:  ${BLUE}./RECOVER_FROM_CRASH.sh${NC}"
echo ""

# 6. Quick health check
echo -e "${BOLD}Quick Health Check:${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Backend health
if curl -s http://localhost:8000/health &> /dev/null; then
    echo -e "  ${GREEN}✓ Backend API:${NC}     http://localhost:8000 (healthy)"
else
    echo -e "  ${RED}✗ Backend API:${NC}     Not responding"
fi

# Check if mobile is running
if lsof -ti:8081 &> /dev/null; then
    echo -e "  ${GREEN}✓ Mobile Dev:${NC}      http://localhost:8081 (running)"
else
    echo -e "  ${YELLOW}⚠ Mobile Dev:${NC}      Not running"
fi

# Check if web is running
if lsof -ti:3000 &> /dev/null; then
    echo -e "  ${GREEN}✓ Web Admin:${NC}       http://localhost:3000 (running)"
else
    echo -e "  ${YELLOW}⚠ Web Admin:${NC}       Not running"
fi

echo ""
echo -e "${BOLD}${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║     Recovery Analysis Complete ✓          ║${NC}"
echo -e "${BOLD}${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
