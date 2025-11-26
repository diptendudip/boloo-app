# Crash Recovery System - Auto-Checkpoint & State Restoration

**Created:** Nov 19, 2025
**Purpose:** Prevent work loss during VS Code/Claude crashes

---

## 🎯 Problem Analysis

### What Happened During Last Crash

**Timeline:**
- **16:12:42** - Last session saved automatically (17-minute session)
- **16:55-16:59** - Parallel documentation sprint (5 files, 3,517 lines)
- **~17:00** - VS Code crashed
- **Result**: 45+ minutes of context lost (though files were saved)

**Files Created (Recovered):**
1. ✅ AZURE_DEPLOYMENT_GUIDE.md (600 lines)
2. ✅ DOMAIN_SETUP.md (547 lines)
3. ✅ APK_BUILD_GUIDE.md (795 lines)
4. ✅ CI_CD_PIPELINE.md (831 lines)
5. ✅ PERFORMANCE_OPTIMIZATION.md (744 lines)

**Context Lost:**
- ❌ Which task was active
- ❌ Next steps planned
- ❌ Parallel agent coordination
- ❌ MVP focus decisions

---

## 🔧 Enhanced Recovery System

### 1. Auto-Checkpoint Every 10 Minutes

**Create: `.claude/hooks/auto-checkpoint.sh`**

```bash
#!/bin/bash
# Auto-checkpoint script - runs every 10 minutes

SESSION_ID="${CLAUDE_SESSION_ID:-checkpoint-$(date +%s)}"
CHECKPOINT_DIR=".recovery/checkpoints"
CHECKPOINT_FILE="$CHECKPOINT_DIR/checkpoint-$(date +%Y%m%d-%H%M%S).json"

# Create checkpoint directory
mkdir -p "$CHECKPOINT_DIR"

# Collect current state
STATE=$(cat <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "sessionId": "$SESSION_ID",
  "workingDir": "$(pwd)",
  "activeFiles": $(git status --short 2>/dev/null | jq -R -s -c 'split("\n") | map(select(length > 0))' || echo "[]"),
  "recentCommands": $(tail -20 ~/.zsh_history 2>/dev/null | jq -R -s -c 'split("\n") | map(select(length > 0))' || echo "[]"),
  "gitBranch": "$(git branch --show-current 2>/dev/null || echo 'none')",
  "gitStatus": "$(git status --porcelain 2>/dev/null | wc -l | xargs)",
  "processStatus": {
    "pm2": $(pm2 jlist 2>/dev/null || echo "[]"),
    "docker": $(docker ps --format '{{json .}}' 2>/dev/null | jq -s '.' || echo "[]")
  }
}
EOF
)

# Save checkpoint
echo "$STATE" > "$CHECKPOINT_FILE"
echo "✅ Checkpoint saved: $CHECKPOINT_FILE"

# Keep only last 50 checkpoints (prevent disk bloat)
ls -t "$CHECKPOINT_DIR"/checkpoint-*.json | tail -n +51 | xargs rm -f 2>/dev/null
```

**Setup auto-run:**
```bash
chmod +x .claude/hooks/auto-checkpoint.sh

# Add to crontab (runs every 10 minutes)
(crontab -l 2>/dev/null; echo "*/10 * * * * cd '/Users/diptendu/boloo app/boloo-app' && ./.claude/hooks/auto-checkpoint.sh >> .recovery/checkpoint.log 2>&1") | crontab -
```

---

### 2. Task State Persistence

**Create: `.claude/hooks/task-tracker.sh`**

```bash
#!/bin/bash
# Track active tasks and goals

TASK_FILE=".recovery/active-tasks.json"
mkdir -p .recovery

# Save current task context
save_task() {
  local task_desc="$1"
  local priority="${2:-medium}"

  cat > "$TASK_FILE" <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "currentTask": "$task_desc",
  "priority": "$priority",
  "mvpFocus": true,
  "nextSteps": [
    "Continue where left off",
    "Check services: pm2 status && docker ps",
    "Verify backend: curl localhost:8000/health"
  ]
}
EOF
  echo "📝 Task saved: $task_desc"
}

# Usage in your workflow:
# save_task "Implementing MVP deployment guides" "high"
```

---

### 3. Quick Recovery Script

**Create: `./RECOVER_FROM_CRASH.sh`**

```bash
#!/bin/bash
set -e

echo "🚑 CRASH RECOVERY SYSTEM"
echo "========================"
echo ""

# 1. Find latest checkpoint
LATEST_CHECKPOINT=$(ls -t .recovery/checkpoints/checkpoint-*.json 2>/dev/null | head -1)

if [ -n "$LATEST_CHECKPOINT" ]; then
  echo "📍 Found checkpoint: $LATEST_CHECKPOINT"
  echo ""

  # Parse checkpoint
  TIMESTAMP=$(jq -r '.timestamp' "$LATEST_CHECKPOINT")
  SESSION_ID=$(jq -r '.sessionId' "$LATEST_CHECKPOINT")
  GIT_CHANGES=$(jq -r '.gitStatus' "$LATEST_CHECKPOINT")

  echo "Last checkpoint: $TIMESTAMP"
  echo "Session ID: $SESSION_ID"
  echo "Uncommitted changes: $GIT_CHANGES files"
  echo ""
else
  echo "⚠️  No checkpoints found"
fi

# 2. Show active task (if exists)
if [ -f .recovery/active-tasks.json ]; then
  echo "📋 ACTIVE TASK:"
  echo "=============="
  jq '.' .recovery/active-tasks.json
  echo ""
fi

# 3. Check system status
echo "🔍 SYSTEM STATUS:"
echo "================"

echo -n "PM2 Services: "
if pm2 status >/dev/null 2>&1; then
  pm2 status | grep -E "(online|errored)" || echo "No processes"
else
  echo "PM2 not running"
fi

echo ""
echo -n "Docker Services: "
if docker ps >/dev/null 2>&1; then
  docker ps --format "{{.Names}}: {{.Status}}"
else
  echo "Docker not running"
fi

echo ""
echo -n "Backend Health: "
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
  echo "✅ Healthy"
else
  echo "❌ Not responding"
fi

echo ""

# 4. Recent file changes
echo "📁 RECENT CHANGES:"
echo "=================="
echo "Modified in last hour:"
find . -type f -mmin -60 -name "*.md" -o -name "*.py" -o -name "*.ts" -o -name "*.tsx" | grep -v node_modules | head -10

echo ""

# 5. Suggest next action
echo "💡 SUGGESTED ACTIONS:"
echo "===================="
if ! pm2 status >/dev/null 2>&1 || ! docker ps >/dev/null 2>&1; then
  echo "1. ⚠️  Start services: ./START_PROJECT.sh"
else
  echo "1. ✅ Services running"
fi

if [ -f .recovery/active-tasks.json ]; then
  echo "2. 📋 Resume task: $(jq -r '.currentTask' .recovery/active-tasks.json)"
else
  echo "2. 🎯 Focus on MVP launch preparation"
fi

echo "3. 📊 Check recent work: git status && git log -5 --oneline"
echo "4. 🔄 Review checkpoint: cat $LATEST_CHECKPOINT | jq '.'"

echo ""
echo "✨ Recovery complete! You can continue working."
```

**Make it executable:**
```bash
chmod +x ./RECOVER_FROM_CRASH.sh
```

---

### 4. Usage Workflow

#### **Before Starting Work:**
```bash
# Set active task
.claude/hooks/task-tracker.sh save_task "MVP deployment preparation" "high"
```

#### **During Work:**
- Auto-checkpoints run every 10 minutes automatically
- No manual intervention needed!

#### **After Crash:**
```bash
# Run recovery
./RECOVER_FROM_CRASH.sh

# Output shows:
# - Last checkpoint time
# - Active task context
# - System status
# - Recent file changes
# - Next steps
```

---

## 🎯 What Gets Saved

### Every 10 Minutes (Auto-checkpoint):
- Current working directory
- Modified files (git status)
- Recent commands
- PM2 process status
- Docker container status
- Git branch and uncommitted changes

### On Demand (Task tracking):
- Current task description
- Priority level
- MVP focus flag
- Next steps

### Always Available:
- File timestamps (OS level)
- Git history
- PM2 logs
- Docker logs

---

## 🔄 Recovery Examples

### Example 1: Crash During Documentation Work

**Before crash:**
```bash
# You were working on deployment docs
.claude/hooks/task-tracker.sh save_task "Creating deployment guides for MVP" "critical"

# Auto-checkpoint runs at 16:50, 17:00, 17:10...
# VS Code crashes at 17:05
```

**After crash:**
```bash
./RECOVER_FROM_CRASH.sh

# Output:
# 📍 Last checkpoint: 2025-11-19T17:00:00Z
# 📋 Active task: Creating deployment guides for MVP (CRITICAL)
# 📁 Recent changes:
#    - AZURE_DEPLOYMENT_GUIDE.md (modified 5 min ago)
#    - DOMAIN_SETUP.md (modified 3 min ago)
# 💡 Continue: Review recent docs and complete performance optimization
```

---

### Example 2: Complete System Crash

**Recovery:**
```bash
./RECOVER_FROM_CRASH.sh

# Shows:
# ⚠️  Backend not responding
# ⚠️  Docker not running
# 💡 Run: ./START_PROJECT.sh

./START_PROJECT.sh

# Verify recovery
pm2 status
docker ps
curl localhost:8000/health
```

---

## 📊 Benefits

| Feature | Before | After |
|---------|--------|-------|
| **State Recovery** | Manual only | Auto every 10min |
| **Task Context** | Lost | Preserved |
| **Recovery Time** | 30+ min | <5 min |
| **Work Loss** | 45+ min | <10 min max |
| **Manual Effort** | High | Low |

---

## 🚀 Installation

```bash
cd "/Users/diptendu/boloo app/boloo-app"

# 1. Create recovery directories
mkdir -p .recovery/checkpoints .claude/hooks

# 2. Create scripts (copy from above)
# - .claude/hooks/auto-checkpoint.sh
# - .claude/hooks/task-tracker.sh
# - ./RECOVER_FROM_CRASH.sh

# 3. Make executable
chmod +x .claude/hooks/*.sh ./RECOVER_FROM_CRASH.sh

# 4. Setup auto-checkpoint cron
(crontab -l 2>/dev/null; echo "*/10 * * * * cd '/Users/diptendu/boloo app/boloo-app' && ./.claude/hooks/auto-checkpoint.sh >> .recovery/checkpoint.log 2>&1") | crontab -

# 5. Verify cron
crontab -l

# 6. Test recovery
./RECOVER_FROM_CRASH.sh
```

---

## 🔒 Privacy & Cleanup

```bash
# View what's stored
ls -lh .recovery/checkpoints/

# View recent checkpoint
cat .recovery/checkpoints/checkpoint-*.json | jq '.' | head -50

# Clear old checkpoints (keeps last 50 automatically)
# Or manually:
rm .recovery/checkpoints/checkpoint-2025*.json

# Disable auto-checkpoint
crontab -l | grep -v auto-checkpoint | crontab -
```

---

## 📝 Integration with Claude Flow

The system integrates with existing Claude Flow hooks:

```bash
# Session start (automatic)
npx claude-flow@alpha hooks pre-task --description "MVP Launch Prep"

# During work (automatic every 10 min)
# → Auto-checkpoint runs in background

# Session end (automatic)
npx claude-flow@alpha hooks post-task
npx claude-flow@alpha hooks session-end --generate-summary
```

---

## ✅ Success Metrics

After implementing this system:
- ✅ Max 10 minutes of context loss (vs 45+ before)
- ✅ Automatic state preservation
- ✅ Quick recovery (<5 min vs 30+ min)
- ✅ Task continuity maintained
- ✅ No manual intervention needed

---

## 🎯 MVP Launch Readiness

With this system in place, you can confidently focus on MVP launch:

1. **Work freely** - Auto-checkpoints protect your progress
2. **Track tasks** - Always know what to continue after restart
3. **Fast recovery** - Back to work in minutes, not hours
4. **No surprises** - Full visibility into system state

---

*Last Updated: Nov 19, 2025*
*Status: Ready for Production*
