#!/bin/bash
# build-init.sh — Build init.zip from current mc-init state
# Usage: bash scripts/build-init.sh [version_tag]
# Output: versions/current/init.zip + manifest.json

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION_TAG="${1:-$(date +%Y-%m-%d-%H%M%S)}"
CURRENT="$REPO_ROOT/versions/current"
WORK="$REPO_ROOT/versions/build-$VERSION_TAG"
INIT_DIR="$WORK/init"

echo "=== mc-init build: $VERSION_TAG ==="

# Clean previous build
rm -rf "$WORK"
mkdir -p "$INIT_DIR"

# Copy core init files
echo "Copying init core..."
cp "$REPO_ROOT/init.py" "$INIT_DIR/"
cp "$REPO_ROOT/init_prompt.md" "$INIT_DIR/"
cp "$REPO_ROOT/README.md" "$INIT_DIR/"

# Copy src
echo "Copying src..."
cp -r "$REPO_ROOT/src" "$INIT_DIR/"

# Copy seeds
echo "Copying seeds..."
mkdir -p "$INIT_DIR/seeds"
cp "$REPO_ROOT/seeds/"* "$INIT_DIR/seeds/" 2>/dev/null || true

# Copy controllers
echo "Copying controllers..."
mkdir -p "$INIT_DIR/controllers"
cp "$REPO_ROOT/controllers/"* "$INIT_DIR/controllers/" 2>/dev/null || true

# Copy docs
echo "Copying docs..."
mkdir -p "$INIT_DIR/docs"
cp "$REPO_ROOT/docs/"* "$INIT_DIR/docs/" 2>/dev/null || true

# Copy default skills
echo "Copying default skills..."
mkdir -p "$INIT_DIR/skills/core-common"
cp -r "$REPO_ROOT/defaults/core-common/"* "$INIT_DIR/skills/core-common/"

# Copy protocol
echo "Copying protocol..."
mkdir -p "$INIT_DIR/protocol"
cp "$REPO_ROOT/protocol/"* "$INIT_DIR/protocol/" 2>/dev/null || true

# Create empty init trigger file
touch "$INIT_DIR/init"

# Create controller update manifest
CURRENT_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SHA256=$(find "$INIT_DIR" -type f -exec sha256sum {} \; | sort -k2 | sha256sum | cut -d' ' -f1)

cat > "$INIT_DIR/controller_update.json" << EOF
{
  "version": "$VERSION_TAG",
  "built_at": "$CURRENT_TIME",
  "builder": "Wilson/Lazarus",
  "repo": "mc-init",
  "content_hash": "$SHA256",
  "default_skills": [
    "file-organization",
    "get-artifact",
    "git-gh",
    "image-gen",
    "meta-gateway",
    "omni-qa",
    "orchestration",
    "plan-mode",
    "storage-explorer"
  ],
  "scope": "Update default skills and seeds for child agent bootstrap"
}
EOF

# Copy allowed signers
cp "$REPO_ROOT/controllers/lazarus_allowed_signers" "$INIT_DIR/controllers/"

# Build ZIP
echo "Building init.zip..."
cd "$WORK"
zip -r init.zip init/ > /dev/null

# Move to current
rm -rf "$CURRENT"
mkdir -p "$CURRENT"
mv init.zip "$CURRENT/"
cp "$INIT_DIR/controller_update.json" "$CURRENT/manifest.json"

# Archive previous if exists
ARCHIVE="$REPO_ROOT/versions/archive/$VERSION_TAG"
if [ -d "$REPO_ROOT/versions/current" ]; then
    mkdir -p "$ARCHIVE"
    cp "$CURRENT/init.zip" "$ARCHIVE/" 2>/dev/null || true
fi

# Clean build dir
rm -rf "$WORK"

# Report
SIZE=$(stat -c%s "$CURRENT/init.zip" 2>/dev/null || echo "unknown")
echo ""
echo "=== Build complete ==="
echo "Version: $VERSION_TAG"
echo "File: versions/current/init.zip"
echo "Size: $SIZE bytes"
echo "Hash: $SHA256"
echo "Skills: $(ls "$REPO_ROOT/defaults/core-common" | tr '\n' ' ')"
