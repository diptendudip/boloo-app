#!/bin/bash
# Auto-Checkpoint System for Crash Recovery
# Purpose: Automatically save work context every 10 minutes
# Created: 2025-11-22

set -e

# Configuration
CHECKPOINT_DIR=".recovery/checkpoints"
MAX_CHECKPOINTS=10
CHECKPOINT_INTERVAL=600  # 10 minutes in seconds

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Create checkpoint directory
mkdir -p "$CHECKPOINT_DIR"

# Function to create checkpoint
create_checkpoint() {
    local timestamp=$(date -u +"%Y%m%d_%H%M%S")
    local checkpoint_file="$CHECKPOINT_DIR/checkpoint_${timestamp}.json"

    echo -e "${BLUE}📸 Creating checkpoint: ${timestamp}${NC}"

    # Collect context
    local git_branch=$(git branch --show-current 2>/dev/null || echo "no-git")
    local git_status=$(git status --short 2>/dev/null | wc -l | tr -d ' ')
    local recent_files=$(find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.md" \) -not -path "*/node_modules/*" -not -path "*/.git/*" -mmin -60 | head -10)
    local pm2_status=$(pm2 jlist 2>/dev/null || echo "[]")
    local docker_status=$(docker ps --format "{{.Names}}: {{.Status}}" 2>/dev/null || echo "not running")

    # Create checkpoint JSON
    cat > "$checkpoint_file" <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "local_time": "$(date +"%Y-%m-%d %H:%M:%S")",
  "git": {
    "branch": "$git_branch",
    "uncommitted_changes": $git_status,
    "recent_commits": [
$(git log --oneline -3 --format='      "%h - %s"' 2>/dev/null | paste -sd "," - || echo '      "no commits"')
    ]
  },
  "recent_files_modified": [
$(echo "$recent_files" | sed 's/^/    "/' | sed 's/$/"/' | paste -sd "," - || echo '    "none"')
  ],
  "services": {
    "pm2": $(echo "$pm2_status" | jq -c '.' 2>/dev/null || echo '[]'),
    "docker": "$(echo "$docker_status" | head -3)"
  },
  "working_directory": "$(pwd)"
}
EOF

    echo -e "${GREEN}✓ Checkpoint saved: ${checkpoint_file}${NC}"

    # Cleanup old checkpoints (keep only last MAX_CHECKPOINTS)
    local checkpoint_count=$(ls -1 "$CHECKPOINT_DIR"/checkpoint_*.json 2>/dev/null | wc -l | tr -d ' ')
    if [ "$checkpoint_count" -gt "$MAX_CHECKPOINTS" ]; then
        local to_delete=$((checkpoint_count - MAX_CHECKPOINTS))
        ls -1t "$CHECKPOINT_DIR"/checkpoint_*.json | tail -n "$to_delete" | xargs rm -f
        echo -e "${YELLOW}🧹 Cleaned up ${to_delete} old checkpoints${NC}"
    fi
}

# Function to run continuous checkpointing
run_continuous() {
    echo -e "${GREEN}🚀 Auto-Checkpoint System Started${NC}"
    echo -e "${BLUE}Checkpoints will be saved every $(($CHECKPOINT_INTERVAL / 60)) minutes${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""

    while true; do
        create_checkpoint
        sleep "$CHECKPOINT_INTERVAL"
    done
}

# Function to create manual checkpoint
manual_checkpoint() {
    create_checkpoint
    echo ""
    echo -e "${GREEN}Manual checkpoint created successfully!${NC}"
}

# Main script logic
case "${1:-continuous}" in
    continuous)
        run_continuous
        ;;
    manual)
        manual_checkpoint
        ;;
    once)
        manual_checkpoint
        ;;
    *)
        echo "Usage: $0 {continuous|manual|once}"
        echo "  continuous - Run continuous checkpointing (default)"
        echo "  manual     - Create single checkpoint now"
        echo "  once       - Same as manual"
        exit 1
        ;;
esac
