#!/usr/bin/env python3
"""
Manage batch watchers: list, kill, view logs.

Usage:
  manage_watchers.py list
  manage_watchers.py kill <batch_id>
  manage_watchers.py logs <batch_id>
  manage_watchers.py cleanup  # remove stale entries
"""

import json
import os
import sys
import subprocess
from datetime import datetime

ACTIVE_BATCHES = os.path.expanduser("~/.hermes/logs/watchers/active_batches.json")
WATCHER_LOGS = os.path.expanduser("~/.hermes/logs/watchers")


def load_active():
    """Load active batches"""
    try:
        with open(ACTIVE_BATCHES, 'r') as f:
            return json.load(f)
    except:
        return {}


def list_watchers():
    """List active watchers"""
    active = load_active()

    if not active:
        print("No active watchers")
        return

    print(f"📋 Active Watchers ({len(active)})")
    print("=" * 60)

    for batch_id, info in active.items():
        started = datetime.fromisoformat(info['started_at'])
        age = (datetime.now() - started).total_seconds() / 60

        torrents = ', '.join(info['torrents'][:3])
        if len(info['torrents']) > 3:
            torrents += f" ... ({len(info['torrents'])} total)"

        print(f"\n  {batch_id}")
        print(f"    Status: {info['status']}")
        print(f"    Age: {age:.1f} minutes")
        print(f"    PID: {info['pid']}")
        print(f"    Torrents: {torrents}")


def kill_watcher(batch_id):
    """Kill a specific watcher"""
    active = load_active()

    if batch_id not in active:
        print(f"❌ Batch {batch_id} not found")
        sys.exit(1)

    pid = active[batch_id]['pid']

    # Kill the process
    try:
        os.kill(pid, 15)  # SIGTERM
        print(f"✅ Killed watcher {batch_id} (PID {pid})")
    except ProcessLookupError:
        print(f"⚠️ Process {pid} not found (already dead?)")

    # Remove from active
    del active[batch_id]

    with open(ACTIVE_BATCHES, 'w') as f:
        json.dump(active, f, indent=2)


def show_logs(batch_id, tail_lines=50):
    """Show logs for a watcher"""
    log_file = os.path.join(WATCHER_LOGS, f"{batch_id}.log")

    if not os.path.exists(log_file):
        print(f"❌ Log file not found: {log_file}")
        sys.exit(1)

    # Tail the file
    result = subprocess.run(
        ['tail', '-n', str(tail_lines), log_file],
        capture_output=True, text=True
    )

    print(f"📜 Logs for {batch_id} (last {tail_lines} lines):")
    print("=" * 60)
    print(result.stdout)


def cleanup_stale():
    """Remove stale entries (processes that died)"""
    active = load_active()
    to_remove = []

    for batch_id, info in active.items():
        pid = info['pid']

        # Check if process exists
        try:
            os.kill(pid, 0)  # Just check, don't kill
        except ProcessLookupError:
            # Process dead
            to_remove.append(batch_id)
            print(f"🧹 Removing dead watcher: {batch_id}")

    for batch_id in to_remove:
        del active[batch_id]

    with open(ACTIVE_BATCHES, 'w') as f:
        json.dump(active, f, indent=2)

    if to_remove:
        print(f"✅ Cleaned up {len(to_remove)} stale entries")
    else:
        print("✓ No stale entries found")


def main():
    if len(sys.argv) < 2:
        print("Usage: manage_watchers.py [list|kill <batch_id>|logs <batch_id>|cleanup]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        list_watchers()
    elif command == "kill":
        if len(sys.argv) < 3:
            print("Usage: manage_watchers.py kill <batch_id>")
            sys.exit(1)
        kill_watcher(sys.argv[2])
    elif command == "logs":
        if len(sys.argv) < 3:
            print("Usage: manage_watchers.py logs <batch_id>")
            sys.exit(1)
        show_logs(sys.argv[3] if len(sys.argv) > 3 else sys.argv[2])
    elif command == "cleanup":
        cleanup_stale()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()