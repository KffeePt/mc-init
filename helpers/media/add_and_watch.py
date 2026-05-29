#!/usr/bin/env python3
"""
Wrapper for media_search.py add that spawns batch watcher after adding torrents.
Usage: add_and_watch.py --type movie --magnet <magnet> --path <path>
       add_and_watch.py --type show --magnet <magnet1> --magnet <magnet2> --path <path>
"""

import subprocess
import sys
import argparse

MEDIA_SEARCH = "/home/xantastique/.hermes/skills/media/media_search.py"
SPAWN_WATCHER = "/home/xantastique/.hermes/scripts/spawn_watcher.py"

def extract_torrent_name(magnet):
    """Extract torrent name from magnet link"""
    if "dn=" in magnet:
        start = magnet.index("dn=") + 3
        end = magnet.find("&", start)
        if end == -1:
            end = len(magnet)
        from urllib.parse import unquote
        return unquote(magnet[start:end])
    return "Unknown"

def main():
    parser = argparse.ArgumentParser(description="Add torrents and spawn batch watcher")
    parser.add_argument("--magnet", action="append", required=True, help="Magnet link(s)")
    parser.add_argument("--path", required=True, help="Save path")
    parser.add_argument("--type", choices=["movie", "show", "tv", "music"], required=True,
                        help="Explicit media type. Sets qBittorrent category for hook routing.")

    args = parser.parse_args()

    # Add all torrents
    torrent_names = []
    for i, magnet in enumerate(args.magnet):
        result = subprocess.run(
            ["python3", MEDIA_SEARCH, "add", "--magnet", magnet, "--path", args.path, "--type", args.type],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            name = extract_torrent_name(magnet)
            torrent_names.append(name)
            print(f"✅ Added {i+1}/{len(args.magnet)}: {name}")
        else:
            print(f"❌ Failed to add torrent {i+1}")
            sys.exit(1)

    # Spawn watcher for the batch
    print(f"\n🔄 Starting batch watcher for {len(torrent_names)} torrent(s)...")
    subprocess.run(
        ["python3", SPAWN_WATCHER, "--type", args.type] + torrent_names,
        capture_output=False, text=True
    )

if __name__ == "__main__":
    main()