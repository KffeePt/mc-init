#!/bin/bash
# publish-init.sh — Build and publish init.zip to a child agent
# Usage: bash scripts/publish-init.sh <agent_name> [version_tag]
# Supported agents: arby

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENT="${1:-}"
VERSION_TAG="${2:-$(date +%Y-%m-%d-%H%M%S)}"

if [ -z "$AGENT" ]; then
    echo "Usage: bash scripts/publish-init.sh <agent_name> [version_tag]"
    echo "Agents: arby"
    exit 1
fi

# Agent config
case "$AGENT" in
    arby)
        AGENT_IP="100.76.137.32"
        AGENT_USER="santi"
        AGENT_KEY="$HOME/.ssh/id_ed25519_tailscale_homelan"
        AGENT_DEST="C:/Users/santi/init.zip"
        AGENT_INBOX="C:/Users/santi/Documents/Hermes/Comms/arby/inbox"
        ;;
    *)
        echo "Unknown agent: $AGENT"
        exit 1
        ;;
esac

echo "=== mc-init publish to $AGENT ==="

# Build
echo "Building init.zip..."
bash "$REPO_ROOT/scripts/build-init.sh" "$VERSION_TAG"

CURRENT="$REPO_ROOT/versions/current/init.zip"
SHA256=$(sha256sum "$CURRENT" | cut -d' ' -f1)
echo "SHA256: $SHA256"

# SCP to agent
echo "SCP to $AGENT ($AGENT_IP)..."
scp -i "$AGENT_KEY" -o StrictHostKeyChecking=accept-new \
    "$CURRENT" "$AGENT_USER@$AGENT_IP:$AGENT_DEST"

# Verify delivery
echo "Verifying delivery..."
REMOTE_HASH=$(ssh -i "$AGENT_KEY" "$AGENT_USER@$AGENT_IP" \
    "certutil -hashfile '$AGENT_DEST' SHA256" 2>/dev/null | grep -v "CertUtil" | grep -v "^$" | tr -d ' \r\n')

if [ "$REMOTE_HASH" = "$SHA256" ]; then
    echo "HASH MATCH: delivery verified"
else
    echo "HASH MISMATCH!"
    echo "Local:  $SHA256"
    echo "Remote: $REMOTE_HASH"
    exit 1
fi

# Send coordination message
COORD_FILE="/tmp/coordination_${AGENT}_${VERSION_TAG}.json"
cat > "$COORD_FILE" << EOF
{
  "request_id": "$VERSION_TAG",
  "origin_agent": "Wilson/Lazarus",
  "target_agent": "Arby/LilJon",
  "operation_type": "remote_action_request",
  "intent": "Apply updated init.zip with latest default skills and seeds",
  "scope": "Extract init.zip, run 'py .\\\\init.py approved-init --replace-authorized-keys', verify all skills present",
  "risk_level": "low",
  "approval_source": "controller_signed_update",
  "expected_output": "Arby reports successful init update, notifies Xan via Telegram",
  "rollback_or_stop_condition": "If init.py fails, stop and report error",
  "secrets_policy": "no_secrets",
  "init_sha256": "$SHA256",
  "steps": [
    "Expand-Archive -LiteralPath C:\\\\Users\\\\santi\\\\init.zip -DestinationPath C:\\\\Users\\\\santi\\\\init -Force",
    "cd C:\\\\Users\\\\santi\\\\init\\\\init",
    "py .\\\\init.py approved-init --replace-authorized-keys",
    "Verify all default skills present under ~/.hermes/skills/"
  ]
}
EOF

scp -i "$AGENT_KEY" "$COORD_FILE" \
    "$AGENT_USER@$AGENT_IP:$AGENT_INBOX/$(basename "$COORD_FILE")" 2>/dev/null

echo "Coordination message sent to $AGENT inbox"
echo ""
echo "=== Publish complete ==="
echo "Agent: $AGENT"
echo "Version: $VERSION_TAG"
echo "Next: Agent should extract, run init.py, and report back"
