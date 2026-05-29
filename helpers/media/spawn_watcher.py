#!/usr/bin/env python3
"""
Wrapper to spawn a batch watcher in background.
Used by media_search.py add command.
"""

import subprocess
import sys
from pathlib import Path

WATCHER_SCRIPT = Path.home() / ".hermes/scripts/watch_batch.py"

def spawn_watcher(torrent_names, media_type="movie"):
    """Spawn batch watcher in background"""
    if not WATCHER_SCRIPT.exists():
        print(f"⚠️ Watcher script not found: {WATCHER_SCRIPT}")
        return False

    cmd = ["python3", str(WATCHER_SCRIPT), "--type", media_type] + torrent_names

    # Spawn in background, detach from terminal
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        print(f"🔄 Started batch watcher (PID {process.pid}) for {len(torrent_names)} torrent(s)")
        return True
    except Exception as e:
        print(f"⚠️ Failed to spawn watcher: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: spawn_watcher.py [--type movie|show|tv|music] <torrent_name_1> <torrent_name_2> ...")
        sys.exit(1)

    media_type = "movie"
    args = sys.argv[1:]
    if args[:1] == ["--type"]:
        if len(args) < 3:
            print("Usage: spawn_watcher.py [--type movie|show|tv|music] <torrent_name_1> <torrent_name_2> ...")
            sys.exit(1)
        media_type = args[1]
        args = args[2:]

    torrent_names = args
    spawn_watcher(torrent_names, media_type=media_type)