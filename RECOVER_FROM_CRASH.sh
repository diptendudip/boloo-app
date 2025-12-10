#!/bin/bash
set -e

echo "🚑 CRASH RECOVERY SYSTEM"
echo "========================"
echo ""

# 1. Find latest checkpoint
LATEST_CHECKPOINT=$(ls -t .recovery/checkpoints/checkpoint-*.json 2>/dev/null | head -1)

if [ -n "$LATEST_CHECKPOINT" ]; then
  echo "📍 Found checkpoint: $(basename $LATEST_CHECKPOINT)"
  echo ""

  # Parse checkpoint (check if jq is available)
  if command -v jq &> /dev/null; then
    TIMESTAMP=$(jq -r '.timestamp' "$LATEST_CHECKPOINT")
    SESSION_ID=$(jq -r '.sessionId' "$LATEST_CHECKPOINT")
    GIT_CHANGES=$(jq -r '.gitStatus' "$LATEST_CHECKPOINT")

    echo "Last checkpoint: $TIMESTAMP"
    echo "Session ID: $SESSION_ID"
    echo "Uncommitted changes: $GIT_CHANGES files"
  else
    echo "Checkpoint exists but jq not installed (for parsing)"
    echo "Content preview:"
    head -20 "$LATEST_CHECKPOINT"
  fi
  echo ""
else
  echo "⚠️  No checkpoints found (system not initialized yet)"
  echo "   Run: mkdir -p .recovery/checkpoints"
fi

# 2. Show active task (if exists)
if [ -f .recovery/active-tasks.json ]; then
  echo "📋 ACTIVE TASK:"
  echo "=============="
  if command -v jq &> /dev/null; then
    jq '.' .recovery/active-tasks.json
  else
    cat .recovery/active-tasks.json
  fi
  echo ""
fi

# 3. Check system status
echo "🔍 SYSTEM STATUS:"
echo "================"

echo -n "PM2 Services: "
if command -v pm2 &> /dev/null && pm2 status >/dev/null 2>&1; then
  pm2 status | grep -E "(online|errored)" || echo "No processes running"
else
  echo "PM2 not running (run: ./START_PROJECT.sh)"
fi

echo ""
echo -n "Docker Services: "
if command -v docker &> /dev/null && docker ps >/dev/null 2>&1; then
  docker ps --format "{{.Names}}: {{.Status}}"
else
  echo "Docker not running (start Docker Desktop)"
fi

echo ""
echo -n "Backend Health: "
if curl -s -f http://localhost:8000/health >/dev/null 2>&1; then
  echo "✅ Healthy"
else
  echo "❌ Not responding (run: ./START_PROJECT.sh)"
fi

echo ""

# 4. Recent file changes
echo "📁 RECENT CHANGES (last hour):"
echo "=============================="
find . -type f -mmin -60 \( -name "*.md" -o -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.sh" \) \
  -not -path "*/node_modules/*" \
  -not -path "*/.git/*" \
  -not -path "*/venv/*" \
  -not -path "*/__pycache__/*" 2>/dev/null | head -15 || echo "None"

echo ""

# 5. Suggest next action
echo "💡 SUGGESTED ACTIONS:"
echo "===================="

SERVICES_DOWN=false
if ! (command -v pm2 &> /dev/null && pm2 status >/dev/null 2>&1) || ! (command -v docker &> /dev/null && docker ps >/dev/null 2>&1); then
  echo "1. ⚠️  Start services: ./START_PROJECT.sh"
  SERVICES_DOWN=true
else
  echo "1. ✅ Services running"
fi

if [ -f .recovery/active-tasks.json ] && command -v jq &> /dev/null; then
  ACTIVE_TASK=$(jq -r '.currentTask' .recovery/active-tasks.json 2>/dev/null || echo "Unknown")
  echo "2. 📋 Resume task: $ACTIVE_TASK"
else
  echo "2. 🎯 Focus on MVP launch preparation"
fi

echo "3. 📊 Check recent work: git status && git log -5 --oneline"

if [ -n "$LATEST_CHECKPOINT" ] && command -v jq &> /dev/null; then
  echo "4. 🔄 Review checkpoint: cat $LATEST_CHECKPOINT | jq '.'"
fi

echo ""

if [ "$SERVICES_DOWN" = true ]; then
  echo "⚡ QUICK START: ./START_PROJECT.sh"
else
  echo "✨ Recovery complete! All systems operational. You can continue working."
fi
