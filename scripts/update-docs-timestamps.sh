#!/bin/bash

# update-docs-timestamps.sh
# Automatically updates "Last Updated" timestamps in all documentation
# Usage: ./scripts/update-docs-timestamps.sh [optional-file-pattern]

set -e

TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M UTC")
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "📝 Updating documentation timestamps..."
echo "🕐 Current time: $TIMESTAMP"
echo "📂 Root directory: $ROOT_DIR"
echo ""

# Function to update timestamp in a file
update_timestamp() {
    local file=$1
    local temp_file="${file}.tmp"

    # Check if file has "Last Updated" or "last_updated" marker
    if grep -q -E "(Last Updated|last_updated):" "$file"; then
        echo "  ✓ Updating: $file"

        # Update YAML frontmatter style
        sed -E "s/^last_updated:.*$/last_updated: \"$TIMESTAMP\"/" "$file" > "$temp_file"

        # Update Markdown header style
        sed -E "s/\*\*Last Updated\*\*:.*/\*\*Last Updated\*\*: $TIMESTAMP/" "$temp_file" > "${temp_file}.2"
        mv "${temp_file}.2" "$temp_file"

        # Replace original if changes were made
        if ! cmp -s "$file" "$temp_file"; then
            mv "$temp_file" "$file"
            echo "    ✅ Updated timestamp"
        else
            rm "$temp_file"
            echo "    ℹ️  No changes needed"
        fi
    else
        echo "  ⚠️  No timestamp marker found in: $file"
    fi
}

# Find all markdown files (excluding node_modules)
if [ -n "$1" ]; then
    # Update specific pattern if provided
    FILES=$(find "$ROOT_DIR" -name "$1" -type f ! -path "*/node_modules/*")
else
    # Update all markdown files
    FILES=$(find "$ROOT_DIR" -name "*.md" -type f ! -path "*/node_modules/*")
fi

COUNT=0
for file in $FILES; do
    update_timestamp "$file"
    ((COUNT++))
done

echo ""
echo "✅ Processed $COUNT files"
echo ""

# Update CHANGELOG if exists
if [ -f "$ROOT_DIR/CHANGELOG.md" ]; then
    echo "📋 Updating CHANGELOG.md metadata..."
    sed -i.bak "s/Last Updated:.*/Last Updated: $TIMESTAMP/" "$ROOT_DIR/CHANGELOG.md"
    rm "$ROOT_DIR/CHANGELOG.md.bak" 2>/dev/null || true
    echo "  ✅ CHANGELOG updated"
fi

# Update documentation index if exists
if [ -f "$ROOT_DIR/docs/DOCUMENTATION_INDEX.md" ]; then
    echo "📚 Updating DOCUMENTATION_INDEX.md..."
    sed -i.bak "s/Last Updated:.*/Last Updated: $TIMESTAMP/" "$ROOT_DIR/docs/DOCUMENTATION_INDEX.md"
    sed -i.bak "s/Last Audit:.*/Last Audit: $TIMESTAMP/" "$ROOT_DIR/docs/DOCUMENTATION_INDEX.md"
    rm "$ROOT_DIR/docs/DOCUMENTATION_INDEX.md.bak" 2>/dev/null || true
    echo "  ✅ Documentation index updated"
fi

echo ""
echo "🎉 Documentation timestamps updated successfully!"
echo ""
echo "Next steps:"
echo "  1. Review changes: git diff"
echo "  2. Commit changes: git add . && git commit -m 'docs: update timestamps'"
echo ""
