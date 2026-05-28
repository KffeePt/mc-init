"""Show gap analyzer — compare local episodes against TVmaze database.

TVmaze provides free, no-key-required API with comprehensive episode data:
  - Search: GET /search/shows?q=<query>
  - Episodes: GET /shows/<id>/episodes
  - Seasons: GET /shows/<id>/seasons
"""

import os
import re
from typing import Dict, Any, List, Optional

from .base import BaseGapAnalyzer, GapResult


class ShowGapAnalyzer(BaseGapAnalyzer):
    """Analyze gaps in a TV show library by comparing local files against TVmaze."""

    DEFAULT_LIBRARY_PATH = "/mnt/f/Shows/"
    TVMAZE_BASE = "https://api.tvmaze.com"

    def analyze(self, query: str, library_path: Optional[str] = None) -> GapResult:
        result = GapResult(media_type="show", query=query)

        # 1. Find show on TVmaze
        show_data = self._find_show(query)
        if not show_data:
            result.metadata["error"] = "Show not found on TVmaze"
            return result

        show_id = show_data["id"]
        show_name = show_data["name"]
        result.source = "TVmaze"
        result.metadata["show_name"] = show_name
        result.metadata["show_id"] = show_id
        result.metadata["status"] = show_data.get("status", "Unknown")
        result.metadata["premiered"] = show_data.get("premiered", "Unknown")

        # 2. Get all episodes from TVmaze
        episodes = self._get_episodes(show_id)
        if not episodes:
            result.metadata["error"] = "Could not fetch episode list"
            return result

        result.total_expected = len(episodes)

        # 3. Scan local library for existing episodes
        lib_path = library_path or self.DEFAULT_LIBRARY_PATH
        existing_codes = self._scan_local_episodes(lib_path, query)

        # 4. Classify each episode as existing or missing
        for ep in episodes:
            season = ep.get("season", 0)
            number = ep.get("number", 0)
            name = ep.get("name", "Unknown")
            code = f"S{season:02d}E{number:02d}"

            entry = {
                "code": code,
                "season": season,
                "episode": number,
                "name": name,
                "airdate": ep.get("airdate", ""),
            }

            if code in existing_codes:
                result.existing.append(entry)
            else:
                # Skip unaired episodes (future)
                airdate = ep.get("airdate", "")
                if airdate and airdate > "2026-05-24":
                    entry["unaired"] = True
                result.missing.append(entry)

        # 5. Organize by season
        result.metadata["seasons"] = self._organize_by_season(episodes, existing_codes)

        return result

    def search_missing(self, gap_result: GapResult) -> Dict[str, Any]:
        """Search for missing episodes on torrent indexers."""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from lib.search import SearchEngine

        engine = SearchEngine()
        search_results = {}

        # Group missing by season for efficient searching
        missing_by_season: Dict[int, List[Dict]] = {}
        for item in gap_result.missing:
            if item.get("unaired"):
                continue
            s = item["season"]
            missing_by_season.setdefault(s, []).append(item)

        show_name = gap_result.metadata.get("show_name", gap_result.query)

        # Search for season bundles first (more efficient)
        for season_num in sorted(missing_by_season.keys()):
            season_eps = missing_by_season[season_num]
            # If whole season is missing, search for season bundle
            if len(season_eps) >= 3:
                query = show_name + " S" + f"{season_num:02d}"
                data = engine.search(query, media_type="show", limit=5)
                search_results[query] = data

        # Search for individual episodes if few are missing
        for item in gap_result.missing:
            if item.get("unaired"):
                continue
            code = item["code"]
            query = show_name + " " + code
            data = engine.search(query, media_type="show", limit=5)
            search_results[code] = data

        return search_results

    def _find_show(self, query: str) -> Optional[Dict]:
        """Search TVmaze for a show and return the best match."""
        import urllib.parse
        encoded = urllib.parse.quote(query, safe="")
        url = self.TVMAZE_BASE + "/search/shows?q=" + encoded

        data = self._fetch_json(url)
        if not data or not isinstance(data, list) or len(data) == 0:
            return None

        # Get the top result
        top = data[0].get("show", data[0])
        score = data[0].get("score", 0)

        # Reject low-relevance matches (<0.5 means poor string similarity)
        if score < 0.5:
            # Try to warn about potential mismatch
            show_name = top.get("name", "Unknown")
            query_lower = query.lower()
            show_lower = show_name.lower()
            # If query words don't significantly overlap with show name, it's likely wrong
            q_words = set(query_lower.split()) - {"the", "a", "an", "and", "of"}
            s_words = set(show_lower.split()) - {"the", "a", "an", "and", "of"}
            overlap = len(q_words & s_words)
            if overlap == 0:
                # Return None to signal "show not found" rather than wrong match
                return None

        return top

    def _get_episodes(self, show_id: int) -> List[Dict]:
        """Fetch all episodes for a show from TVmaze."""
        url = self.TVMAZE_BASE + "/shows/" + str(show_id) + "/episodes?specials=0"
        data = self._fetch_json(url)
        if not data or not isinstance(data, list):
            return []
        return data

    def _scan_local_episodes(self, library_path: str, query: str) -> set:
        """Scan local filesystem for existing episodes. Returns set of S##E## codes.

        First finds the show's base directory, then scans it fully regardless of subdir structure.
        """
        codes = set()
        if not os.path.exists(library_path):
            return codes

        query_terms = [t.strip(" .-").lower() for t in query.split() if len(t) > 2]

        # Step 1: Find the show's base directory
        show_base_dir = None
        for entry in os.listdir(library_path):
            entry_path = os.path.join(library_path, entry)
            if not os.path.isdir(entry_path):
                continue
            entry_lower = entry.lower().strip(" .-")
            # Match if enough query terms are in the directory name (fuzzy like Plex)
            match_count = sum(1 for t in query_terms if t in entry_lower)
            if match_count >= len(query_terms) * 0.6:
                show_base_dir = entry_path
                break

        # Step 2: If no exact match, try broader search (partial match)
        if not show_base_dir and query_terms:
            best_match = None
            best_score = 0
            for entry in os.listdir(library_path):
                entry_path = os.path.join(library_path, entry)
                if not os.path.isdir(entry_path):
                    continue
                entry_lower = entry.lower().strip(" .-")
                # Score based on overlapping words
                entry_words = set(entry_lower.split()) - {"the", "a", "an", "and", "of"}
                query_words = set(query_terms)
                overlap = len(entry_words & query_words)
                if overlap > best_score:
                    best_score = overlap
                    best_match = entry_path
            if best_match and best_score > 0:
                show_base_dir = best_match

        # Step 3: Scan the found show directory recursively for all S##E## patterns
        if show_base_dir:
            for root, dirs, files in os.walk(show_base_dir):
                for f in files:
                    fl = f.lower()
                    # Try multiple patterns to catch various naming conventions
                    matches = []

                    # Pattern 1: S##E## (standard)
                    if not matches:
                        matches = re.findall(r's(\d{1,2})e(\d{1,2})', fl, re.I)
                    # Pattern 2: S#_E# or S#-E# (underscore/hyphen separator)
                    if not matches:
                        matches = re.findall(r's(\d+)[_-](?:e|)(\d+)', fl, re.I)
                    # Pattern 3: S#x# or #x# (x separator, with or without S prefix)
                    if not matches:
                        matches = re.findall(r's?(\d+)[x-](\d+)', fl, re.I)
                    # Pattern 4: Season # Episode # (word based)
                    if not matches:
                        matches = re.findall(r'season\s*(\d+)\s*(?:ep|episode)?\s*(\d+)', fl, re.I)

                    if matches:
                        for s, e in matches:
                            codes.add(f"S{int(s):02d}E{int(e):02d}")

        return codes

    @staticmethod
    def _organize_by_season(episodes: List[Dict], existing_codes: set) -> Dict[str, Any]:
        """Organize episode data by season for display."""
        seasons: Dict[int, Dict] = {}

        for ep in episodes:
            s = ep.get("season", 0)
            n = ep.get("number", 0)
            code = f"S{s:02d}E{n:02d}"

            if s not in seasons:
                seasons[s] = {"total": 0, "existing": 0, "missing": 0, "episodes": []}

            seasons[s]["total"] += 1
            if code in existing_codes:
                seasons[s]["existing"] += 1
            else:
                seasons[s]["missing"] += 1

            seasons[s]["episodes"].append({
                "code": code,
                "name": ep.get("name", ""),
                "airdate": ep.get("airdate", ""),
                "status": "✅" if code in existing_codes else "❌",
            })

        return {
            f"Season {s:02d}": {
                "total": v["total"],
                "existing": v["existing"],
                "missing": v["missing"],
                "completion": f"{v['existing']/v['total']*100:.0f}%" if v["total"] > 0 else "0%",
            }
            for s, v in sorted(seasons.items())
        }
