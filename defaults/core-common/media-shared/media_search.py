#!/usr/bin/env python3
"""
Media Search Tool — Unified torrent search, download status, and malware scanning.

Usage:
  python3 media_search.py search --type movie --query "Inception 2010"
  python3 media_search.py search --type show --query "Breaking Bad"
  python3 media_search.py search --type music --query "Radiohead OK Computer FLAC"
  python3 media_search.py status [--filter "Breaking Bad"]
  python3 media_search.py scan --path /mnt/d/Movies/
  python3 media_search.py add --type movie --magnet "magnet:?..." --path "D:\\Movies\\"
"""

import argparse
import json
import sys

# Add lib/ to path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.search import SearchEngine
from lib.qbittorrent import QBittorrentClient
from lib.scanner import MalwareScanner
from lib.gap import get_analyzer
from lib.formatters import ResultFormatter, StatusFormatter, ScanFormatter, GapFormatter


def cmd_search(args):
    engine = SearchEngine()
    formatter = ResultFormatter()

    data = engine.search(args.query, media_type=args.type, limit=args.limit)

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(formatter.format(data, media_type=args.type))


def cmd_status(args):
    client = QBittorrentClient()
    formatter = StatusFormatter()

    data = client.get_torrents(filter_name=getattr(args, "filter", None))
    print(formatter.format(data))


def cmd_scan(args):
    scanner = MalwareScanner()
    formatter = ScanFormatter()

    data = scanner.scan(args.path, quick=not args.full)

    if args.json:
        print(json.dumps(data, indent=2, default=str))
    else:
        print(formatter.format(data))


def cmd_add(args):
    client = QBittorrentClient()

    result = client.add_torrent(args.magnet, args.path, media_type=getattr(args, "type", None))
    if result["status"] == "ok":
        print("✅ " + result["message"])
    else:
        print("❌ " + result["message"])


def cmd_gap(args):
    analyzer = get_analyzer(args.type)
    formatter = GapFormatter()

    result = analyzer.analyze(args.query, library_path=getattr(args, "library", None))

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, default=str))
    else:
        print(formatter.format(result.to_dict()))

    # If --search flag, also search for missing items
    if args.search_missing and result.missing:
        print("\n\n🔍 Searching for missing items...\n")
        search_results = analyzer.search_missing(result)
        result_formatter = ResultFormatter()
        for key, data in search_results.items():
            formatted = result_formatter.format(data, media_type=args.type)
            if formatted and "No results found" not in formatted:
                print("--- " + key + " ---")
                print(formatted)
                print()


def main():
    parser = argparse.ArgumentParser(
        description="Media search, download management, and malware scanning"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # search
    search_p = subparsers.add_parser("search", help="Search for media")
    search_p.add_argument("--type", choices=["movie", "show", "music"],
                          default="movie", help="Media type")
    search_p.add_argument("--query", required=True, help="Search query")
    search_p.add_argument("--limit", type=int, default=20, help="Max results")
    search_p.add_argument("--json", action="store_true", help="Raw JSON output")

    # status
    status_p = subparsers.add_parser("status", help="Check download status")
    status_p.add_argument("--filter", help="Filter by torrent name")

    # scan
    scan_p = subparsers.add_parser("scan", help="Scan downloads for malware")
    scan_p.add_argument("--path", required=True, help="Path to scan (WSL or Windows)")
    scan_p.add_argument("--full", action="store_true", help="Full scan (slower)")
    scan_p.add_argument("--json", action="store_true", help="Raw JSON output")

    # add
    add_p = subparsers.add_parser("add", help="Add torrent to qBittorrent")
    add_p.add_argument("--magnet", required=True, help="Magnet URI")
    add_p.add_argument("--path", required=True, help="Windows save path")
    add_p.add_argument("--type", choices=["movie", "show", "tv", "music"],
                       required=True,
                       help="Explicit media type; written to qBittorrent category for hook routing")

    # gap analysis
    gap_p = subparsers.add_parser("gap", help="Analyze gaps in local library")
    gap_p.add_argument("--type", choices=["movie", "show", "music"],
                       required=True, help="Media type")
    gap_p.add_argument("--query", required=True, help="Show/artist/movie name")
    gap_p.add_argument("--library", help="Override default library path")
    gap_p.add_argument("--search-missing", action="store_true",
                       help="Also search for missing items on indexers")
    gap_p.add_argument("--json", action="store_true", help="Raw JSON output")

    args = parser.parse_args()

    if args.command == "search":
        cmd_search(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "scan":
        cmd_scan(args)
    elif args.command == "add":
        cmd_add(args)
    elif args.command == "gap":
        cmd_gap(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
