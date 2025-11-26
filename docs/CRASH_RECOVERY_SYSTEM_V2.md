# Crash Recovery System V2.0

**Created:** November 22, 2025
**Purpose:** Automated work recovery after VS Code or system crashes
**Status:** ✅ Production Ready

---

## Overview

The enhanced crash recovery system automatically saves your work context and provides intelligent recovery after crashes. No more lost work or confusion about where you left off!

## Features

### 1. Auto-Checkpoint System ✨
- **Automatic Context Saving:** Every 10 minutes, automatically saves:
  - Recent file modifications
  - Git status and recent commits
  - Running services (PM2, Docker)
  - Working directory
  - Timestamp of work session

- **Smart Cleanup:** Keeps only the last 10 checkpoints to save space

- **Zero Overhead:** Runs in background, doesn't slow down development

### 2. Intelligent Work Recovery 🔍
- **Automatic Detection:** Analyzes what you were working on:
  - Backend development (Python files)
  - Frontend development (TypeScript/React)
  - Documentation (Markdown files)
  - General development

- **Service Status Check:** Verifies all services are running:
  - Backend API (port 8000)
  - Mobile development server (port 8081)
  - Web admin (port 3000)
  - PM2 processes
  - Docker containers

- **Contextual Suggestions:** Provides specific next steps based on detected work

---

## Quick Start

### After Any Crash

Simply run:
```bash
cd "/Users/diptendu/boloo app/boloo-app"
./scripts/recover-work.sh
```

This will:
1. ✅ Find your latest checkpoint
2. ✅ Show what you were working on
3. ✅ Check all service statuses
4. ✅ Suggest specific next steps
5. ✅ Provide quick health check

### Start Auto-Checkpointing

To prevent future work loss, start automatic checkpointing:

```bash
# Terminal 1: Start your regular work
cd "/Users/diptendu/boloo app/boloo-app"
./START_PROJECT.sh

# Terminal 2: Start auto-checkpointing (optional but recommended)
./scripts/auto-checkpoint.sh continuous
```

This runs in the background and saves checkpoints every 10 minutes.

### Manual Checkpoint

Save a checkpoint manually at any time:
```bash
./scripts/auto-checkpoint.sh manual
```

Useful before:
- Making risky changes
- Testing new features
- Deploying to production
- Updating dependencies

---

## How It Works

### Auto-Checkpoint System

**Location:** `scripts/auto-checkpoint.sh`

**What It Saves:**
```json
{
  "timestamp": "2025-11-22T13:30:00Z",
  "git": {
    "branch": "main",
    "uncommitted_changes": 15,
    "recent_commits": ["a1b2c3d - Fix authentication bug", ...]
  },
  "recent_files_modified": [
    "./backend/app/services/auth.py",
    "./mobile/src/screens/LoginScreen.tsx",
    ...
  ],
  "services": {
    "pm2": [...],
    "docker": "..."
  },
  "working_directory": "/Users/diptendu/boloo app/boloo-app"
}
```

**Storage:** `.recovery/checkpoints/checkpoint_YYYYMMDD_HHMMSS.json`

**Retention:** Last 10 checkpoints (older ones auto-deleted)

### Work Recovery Script

**Location:** `scripts/recover-work.sh`

**Analysis Steps:**
1. **Find Latest Checkpoint** - Reads most recent saved state
2. **Analyze File Activity** - Scans files modified in last hour
3. **Check Services** - Verifies PM2, Docker, API endpoints
4. **Detect Context** - Determines what type of work was happening
5. **Suggest Actions** - Provides specific recovery commands

**Output Sections:**
- Last Checkpoint Summary
- Service Status (PM2, Docker)
- Recent File Activity
- Git Status
- Suggested Next Steps
- Quick Health Check

---

## Example Recovery Session

### Scenario: VS Code Crashes During Backend Work

1. **Run Recovery Script:**
```bash
./scripts/recover-work.sh
```

2. **See Output:**
```
╔════════════════════════════════════════════╗
║     Boloo Crash Recovery System v2.0      ║
╚════════════════════════════════════════════╝

📂 Checking for saved checkpoints...
✓ Found checkpoint: checkpoint_20251122_133000.json

Last Checkpoint Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Time:     2025-11-22 13:30:00
  Branch:   main
  Changes:  15 uncommitted files

Recently Modified Files:
  📝 ./backend/app/services/conversation_service.py
  📝 ./backend/tests/test_conversation.py
  📝 ./backend/docs/API_DOCUMENTATION.md

💡 Suggested Next Steps:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Detected: Backend Python development

  1. Check backend logs:
     pm2 logs boloo-backend

  2. Restart backend if needed:
     pm2 restart boloo-backend

  3. Continue backend work:
     cd backend && source venv/bin/activate
```

3. **Follow Suggestions:**
```bash
pm2 logs boloo-backend --lines 50
cd backend && source venv/bin/activate
```

---

## Integration with Existing Systems

### Works With:
- ✅ `START_PROJECT.sh` - Quick recovery system
- ✅ `FULL_RESET.sh` - Full system reset
- ✅ `RECOVER_FROM_CRASH.sh` - Azure deployment recovery
- ✅ PM2 process management
- ✅ Docker container management
- ✅ Git version control

### Complementary Features:
- **START_PROJECT.sh:** Starts all services
- **Auto-Checkpoint:** Saves work context
- **recover-work.sh:** Analyzes and suggests recovery
- **FULL_RESET.sh:** Nuclear option for corrupted state

---

## Automation Options

### Option 1: Run in Background (Recommended)

Add to your `.bashrc` or `.zshrc`:
```bash
# Auto-start checkpointing in boloo project
alias boloo-work='cd "/Users/diptendu/boloo app/boloo-app" && ./START_PROJECT.sh && ./scripts/auto-checkpoint.sh continuous &'
```

Then just type: `boloo-work`

### Option 2: PM2 Management

Add checkpointing to PM2:
```bash
pm2 start ./scripts/auto-checkpoint.sh \
  --name boloo-checkpoint \
  --cron-restart="0 */10 * * *"  # Every 10 minutes

pm2 save
```

### Option 3: Manual Mode

Create checkpoint before risky operations:
```bash
./scripts/auto-checkpoint.sh manual
# ... do risky work ...
```

---

## Checkpoint Management

### View All Checkpoints
```bash
ls -lt .recovery/checkpoints/
```

### View Specific Checkpoint
```bash
cat .recovery/checkpoints/checkpoint_20251122_133000.json | jq '.'
```

### Delete Old Checkpoints
```bash
# Keep only last 5
ls -1t .recovery/checkpoints/checkpoint_*.json | tail -n +6 | xargs rm -f
```

### Backup Checkpoints
```bash
# Before major changes
tar -czf checkpoints-backup-$(date +%Y%m%d).tar.gz .recovery/checkpoints/
```

---

## Troubleshooting

### Issue: "No checkpoints found"

**Cause:** First time using the system or checkpoints expired

**Solution:**
```bash
# Create first checkpoint
./scripts/auto-checkpoint.sh manual

# Or start continuous checkpointing
./scripts/auto-checkpoint.sh continuous &
```

### Issue: "Services not running"

**Cause:** System crashed and services didn't auto-restart

**Solution:**
```bash
# Quick restart
./START_PROJECT.sh

# Or selective restart
pm2 restart all
docker-compose up -d
```

### Issue: "Permission denied"

**Cause:** Scripts not executable

**Solution:**
```bash
chmod +x scripts/*.sh
chmod +x *.sh
```

### Issue: "jq command not found"

**Cause:** jq (JSON parser) not installed

**Solution:**
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq
```

---

## Best Practices

### 1. Regular Checkpointing
- Run auto-checkpoint continuously during development
- Create manual checkpoints before risky changes
- Keep checkpoints for at least 24 hours of work

### 2. Quick Recovery
- Run `recover-work.sh` immediately after any crash
- Follow suggested steps before investigating issues
- Check service status before assuming problems

### 3. Preventive Measures
- Commit important changes to git frequently
- Use staging branches for experimental work
- Keep `.env` files backed up separately

### 4. System Integration
- Add checkpoint automation to startup scripts
- Monitor checkpoint creation in logs
- Review checkpoint data before major deployments

---

## Advanced Usage

### Custom Checkpoint Intervals

Edit `scripts/auto-checkpoint.sh`:
```bash
# Change this line
CHECKPOINT_INTERVAL=600  # 10 minutes

# To this (5 minutes)
CHECKPOINT_INTERVAL=300
```

### Add Custom Context

Extend checkpoint JSON with project-specific data:
```bash
# In auto-checkpoint.sh, add to JSON:
"custom": {
  "current_feature": "authentication",
  "sprint": "sprint-23",
  "blockers": []
}
```

### Notification on Checkpoint

Add to `auto-checkpoint.sh` after checkpoint creation:
```bash
# macOS notification
osascript -e 'display notification "Checkpoint saved" with title "Boloo Dev"'
```

---

## Recovery Workflow Comparison

### Before Crash Recovery System V2.0:
```
1. VS Code crashes
2. ❌ Lost context (what was I working on?)
3. ❌ Check each service manually
4. ❌ Search through files to remember task
5. ❌ 15-30 minutes to recover
```

### With Crash Recovery System V2.0:
```
1. VS Code crashes
2. Run: ./scripts/recover-work.sh
3. ✅ See exactly what you were working on
4. ✅ Check all services in one view
5. ✅ Get specific recovery commands
6. ✅ Back to work in <5 minutes
```

---

## Files Created

| File | Purpose | Frequency |
|------|---------|-----------|
| `scripts/auto-checkpoint.sh` | Creates automatic work checkpoints | Every 10 min |
| `scripts/recover-work.sh` | Analyzes work and suggests recovery | On demand |
| `.recovery/checkpoints/` | Stores checkpoint JSON files | Auto-managed |
| `docs/CRASH_RECOVERY_SYSTEM_V2.md` | This documentation | Updated as needed |

---

## Future Enhancements

### Planned Features:
- [ ] Cloud backup of checkpoints
- [ ] Integration with VS Code workspace state
- [ ] Slack/Email notifications on crash detection
- [ ] ML-based work pattern detection
- [ ] Automatic issue creation for crashes
- [ ] Integration with Azure DevOps
- [ ] Mobile app for remote monitoring

---

## Support

### Quick Reference Commands

```bash
# After crash - immediate recovery
./scripts/recover-work.sh

# Start auto-checkpointing
./scripts/auto-checkpoint.sh continuous &

# Create manual checkpoint
./scripts/auto-checkpoint.sh manual

# View latest checkpoint
cat $(ls -1t .recovery/checkpoints/*.json | head -1) | jq '.'

# Check all services
pm2 status && docker ps

# Restart everything
./START_PROJECT.sh
```

### Documentation
- **Full Recovery Guide:** `docs/RECOVERY_GUIDE.md`
- **Azure Recovery:** `docs/AZURE_DEPLOYMENT_GUIDE.md`
- **Quick Start:** `docs/QUICK_START_GUIDE.md`

### Emergency Contacts
- Recovery scripts location: `/Users/diptendu/boloo app/boloo-app/scripts/`
- Checkpoint storage: `.recovery/checkpoints/`
- Service logs: `~/.pm2/logs/`

---

**Remember:** The best recovery is prevention. Run auto-checkpointing during all development sessions!

---

*Last Updated: November 22, 2025*
*Version: 2.0*
*Status: Production Ready ✅*
