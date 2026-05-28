#!/usr/bin/env python3
"""
Plex Library Refresh Helper

Safely triggers Plex library section scans from WSL/Windows.

Default behavior is intentionally non-destructive/lightweight: list sections only.
Use --section, --section-id, or --all to trigger refreshes.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Iterable

import requests

# From this WSL install, Windows host Plex is reachable through the WSL Hyper-V host IP.
# Override with PLEX_URL if the adapter changes.
PLEX_URL = os.getenv("PLEX_URL", "http://192.168.128.1:32400")
PLEX_TOKEN = os.getenv("PLEX_TOKEN", "")
REQUEST_TIMEOUT = float(os.getenv("PLEX_REFRESH_TIMEOUT", "15"))
DEFAULT_DELAY_SECONDS = float(os.getenv("PLEX_REFRESH_DELAY", "3"))


@dataclass
class PlexSection:
    id: str
    title: str
    type: str
    path: str = ""


def _headers(token: str) -> dict[str, str]:
    return {
        "X-Plex-Token": token,
        "Accept": "application/xml",
    }


def plex_get(base_url: str, path: str, token: str, **kwargs) -> requests.Response:
    return requests.get(
        f"{base_url.rstrip('/')}/{path.lstrip('/')}",
        headers=_headers(token),
        params={"X-Plex-Token": token},  # Plex accepts this even when some header auth paths misbehave.
        timeout=REQUEST_TIMEOUT,
        **kwargs,
    )


def check_identity(base_url: str, token: str) -> str:
    resp = plex_get(base_url, "/identity", token)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    return root.get("version", "unknown")


def get_sections(base_url: str, token: str) -> list[PlexSection]:
    """Fetch all library sections from Plex."""
    resp = plex_get(base_url, "/library/sections", token)
    resp.raise_for_status()

    root = ET.fromstring(resp.text)
    sections: list[PlexSection] = []
    for section in root.findall("Directory"):
        sections.append(
            PlexSection(
                id=section.get("key", ""),
                title=section.get("title", ""),
                type=section.get("type", ""),
                path=section.get("path", ""),
            )
        )
    return sections


def refresh_section(base_url: str, token: str, section_id: str) -> tuple[bool, int, str]:
    """Trigger a refresh on a specific library section.

    Plex's documented endpoint is /library/sections/{id}/refresh. In this environment,
    token-as-query GET has been the most reliable from WSL, while some header-only
    variants can misroute. Keep the request short and do not poll Plex heavily after it.
    """
    url = f"{base_url.rstrip('/')}/library/sections/{section_id}/refresh"
    try:
        resp = requests.get(
            url,
            headers=_headers(token),
            params={"X-Plex-Token": token},
            timeout=REQUEST_TIMEOUT,
        )
        ok = resp.status_code in (200, 201, 202)
        return ok, resp.status_code, resp.text[:200]
    except requests.RequestException as exc:
        return False, 0, str(exc)


def find_section_by_name(sections: Iterable[PlexSection], name: str) -> str | None:
    section_list = list(sections)
    name_lower = name.casefold().strip()

    # Prefer exact matches. Partial-first matching can turn "Shows" into "More Shows".
    for section in section_list:
        if section.title.casefold().strip() == name_lower:
            return section.id

    for section in section_list:
        if name_lower in section.title.casefold():
            return section.id
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely trigger Plex library refresh scans")
    parser.add_argument("--section", help="Refresh specific section by name, e.g. Movies or Shows")
    parser.add_argument("--section-id", type=str, help="Refresh specific numeric section ID")
    parser.add_argument("--all", action="store_true", help="Refresh all sections. Explicit because full scans can stress Plex.")
    parser.add_argument("--token", help="Plex token; overrides PLEX_TOKEN env var")
    parser.add_argument("--url", default=PLEX_URL, help=f"Plex base URL; default: {PLEX_URL}")
    parser.add_argument("--list", action="store_true", help="List sections without refreshing")
    parser.add_argument("--dry-run", action="store_true", help="Show target sections but do not refresh")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS, help="Seconds between section refresh calls")
    args = parser.parse_args()

    token = args.token or PLEX_TOKEN
    if not token:
        print("ERROR: No Plex token provided. Set PLEX_TOKEN or use --token.", file=sys.stderr)
        return 1

    try:
        version = check_identity(args.url, token)
        sections = get_sections(args.url, token)
    except (requests.RequestException, ET.ParseError) as exc:
        print(f"ERROR: Failed to connect to Plex at {args.url}: {exc}", file=sys.stderr)
        print("If Plex is wedged, run Desktop\\restart-plex.bat and retry.", file=sys.stderr)
        return 1

    print(f"Plex OK: {version} @ {args.url}")

    if args.list or (not args.section and not args.section_id and not args.all):
        print("Plex Library Sections:")
        for section in sections:
            print(f"  [{section.id}] {section.title} ({section.type})")
        if not args.list:
            print("\nNo refresh triggered. Use --section, --section-id, or --all.")
        return 0

    section_ids: list[str] = []
    if args.section_id:
        section_ids.append(args.section_id)
    elif args.section:
        section_id = find_section_by_name(sections, args.section)
        if not section_id:
            print(f"ERROR: No section found matching '{args.section}'", file=sys.stderr)
            print("Available sections:", file=sys.stderr)
            for section in sections:
                print(f"  [{section.id}] {section.title}", file=sys.stderr)
            return 1
        section_ids.append(section_id)
    elif args.all:
        section_ids = [s.id for s in sections]

    titles_by_id = {s.id: s.title for s in sections}
    print(f"Target sections: {', '.join(f'[{sid}] {titles_by_id.get(sid, sid)}' for sid in section_ids)}")

    if args.dry_run:
        print("Dry run only. No refresh triggered.")
        return 0

    failures = 0
    for index, sid in enumerate(section_ids):
        ok, status, detail = refresh_section(args.url, token, sid)
        label = titles_by_id.get(sid, sid)
        if ok:
            print(f"  OK: [{sid}] {label} refresh triggered (HTTP {status})")
        else:
            failures += 1
            print(f"  FAIL: [{sid}] {label} refresh failed (HTTP {status}) {detail}")
        if index < len(section_ids) - 1 and args.delay > 0:
            time.sleep(args.delay)

    print("Note: Plex refresh is async. Avoid repeatedly triggering full-library scans.")
    return 2 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
