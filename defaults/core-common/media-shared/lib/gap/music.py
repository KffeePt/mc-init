"""Music gap analyzer — compare local albums against MusicBrainz discography.

MusicBrainz provides free API with comprehensive release data:
  - Artist search: GET /ws/2/artist/?query=<name>&fmt=json
  - Releases: GET /ws/2/artist/<id>/releases?fmt=json&limit=100
  - Release groups (albums): GET /ws/2/release-group?artist=<id>&type=album&fmt=json
"""

import os
import re
from typing import Dict, Any, List, Optional

from .base import BaseGapAnalyzer, GapResult


class MusicGapAnalyzer(BaseGapAnalyzer):
    """Analyze gaps in a music library by comparing local files against MusicBrainz."""

    DEFAULT_LIBRARY_PATH = "/mnt/d/Music/"
    MUSICBRAINZ_BASE = "https://musicbrainz.org/ws/2"

    def analyze(self, query: str, library_path: Optional[str] = None) -> GapResult:
        result = GapResult(media_type="music", query=query)

        # 1. Find artist on MusicBrainz
        artist_data = self._find_artist(query)
        if not artist_data:
            result.metadata["error"] = "Artist not found on MusicBrainz"
            return result

        artist_id = artist_data["id"]
        artist_name = artist_data.get("name", query)
        result.source = "MusicBrainz"
        result.metadata["artist_name"] = artist_name
        result.metadata["artist_id"] = artist_id

        # 2. Get release groups (albums) from MusicBrainz
        albums = self._get_albums(artist_id)
        if not albums:
            result.metadata["error"] = "Could not fetch album list"
            return result

        result.total_expected = len(albums)

        # 3. Scan local library for existing albums
        lib_path = library_path or self.DEFAULT_LIBRARY_PATH
        existing_names = self._scan_local_albums(lib_path, query)

        # 4. Classify each album as existing or missing
        for album in albums:
            title = album.get("title", "Unknown")
            album_id = album.get("id", "")
            first_date = album.get("first-release-date", "")
            album_type = album.get("primary-type", "Album")
            secondary = album.get("secondary-types", [])

            entry = {
                "title": title,
                "id": album_id,
                "date": first_date,
                "type": album_type,
                "secondary_types": secondary,
                "year": first_date[:4] if first_date else "",
            }

            if self._album_exists(title, existing_names):
                result.existing.append(entry)
            else:
                result.missing.append(entry)

        return result

    def search_missing(self, gap_result: GapResult) -> Dict[str, Any]:
        """Search for missing albums on torrent indexers."""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from lib.search import SearchEngine

        engine = SearchEngine()
        search_results = {}

        artist_name = gap_result.metadata.get("artist_name", gap_result.query)

        for item in gap_result.missing:
            title = item["title"]
            year = item.get("year", "")
            query = artist_name + " " + title
            if year:
                query += " " + year
            query += " FLAC"

            data = engine.search(query, media_type="music", limit=5)
            search_results[title] = data

        # Also search for full discography
        discog_query = artist_name + " Discography FLAC"
        data = engine.search(discog_query, media_type="music", limit=5)
        search_results["[Discography]"] = data

        return search_results

    def _find_artist(self, query: str) -> Optional[Dict]:
        """Search MusicBrainz for an artist."""
        import urllib.parse
        encoded = urllib.parse.quote(query, safe="")
        url = self.MUSICBRAINZ_BASE + "/artist/?query=" + encoded + "&fmt=json&limit=5"

        data = self._fetch_json(url, headers={"Accept": "application/json"})
        if not data or "artists" not in data or len(data["artists"]) == 0:
            return None

        return data["artists"][0]

    def _get_albums(self, artist_id: str) -> List[Dict]:
        """Get release groups (albums) for an artist from MusicBrainz."""
        import urllib.parse
        url = (
            self.MUSICBRAINZ_BASE + "/release-group?artist=" + artist_id
            + "&type=album&fmt=json&limit=100&offset=0"
        )

        data = self._fetch_json(url, headers={"Accept": "application/json"})
        if not data or "release-groups" not in data:
            return []

        # Filter to studio albums only (exclude live, compilation, remix, bootleg)
        albums = []
        for rg in data["release-groups"]:
            primary = rg.get("primary-type", "")
            secondary = rg.get("secondary-types", [])

            # Only include studio albums (no secondary types like Live, Compilation, Remix)
            if primary in ("Album",):
                # Skip compilations, live albums, remix albums, and soundtracks
                skip_types = {"Compilation", "Live", "Remix", "Soundtrack", "Spokenword", "Audiobook", "DJ-mix", "Mixtape/Street"}
                if any(t in skip_types for t in secondary):
                    continue
                # Also skip albums with skip words in the title (samplers, deep cuts, etc.)
                title_lower = rg.get("title", "").lower()
                skip_title_words = {"sampler", "deep cuts", "best of", "greatest hits", "essentials", "bonus"}
                if any(w in title_lower for w in skip_title_words):
                    continue
                albums.append({
                    "title": rg.get("title", "Unknown"),
                    "id": rg.get("id", ""),
                    "first-release-date": rg.get("first-release-date", ""),
                    "primary-type": primary,
                    "secondary-types": secondary,
                })

        return albums

    def _scan_local_albums(self, library_path: str, query: str) -> List[str]:
        """Scan local filesystem for existing albums. Returns list of directory names.

        First finds the artist's base directory, then scans all subdirectories for albums.
        """
        albums = []
        if not os.path.exists(library_path):
            return albums

        query_terms = [t.strip(" .-").lower() for t in query.split() if len(t) > 2]

        # Step 1: Find the artist's base directory
        artist_base_dir = None
        for entry in os.listdir(library_path):
            entry_path = os.path.join(library_path, entry)
            if not os.path.isdir(entry_path):
                continue
            entry_lower = entry.lower().strip(" .-")
            match_count = sum(1 for t in query_terms if t in entry_lower)
            if match_count >= len(query_terms) * 0.6:
                artist_base_dir = entry_path
                break

        # Step 2: If no exact match, try broader search
        if not artist_base_dir and query_terms:
            best_match = None
            best_score = 0
            for entry in os.listdir(library_path):
                entry_path = os.path.join(library_path, entry)
                if not os.path.isdir(entry_path):
                    continue
                entry_lower = entry.lower().strip(" .-")
                entry_words = set(entry_lower.split()) - {"the", "a", "an", "and", "of"}
                query_words = set(query_terms)
                overlap = len(entry_words & query_words)
                if overlap > best_score:
                    best_score = overlap
                    best_match = entry_path
            if best_match and best_score > 0:
                artist_base_dir = best_match

        # Step 3: Scan the found artist directory for all album subdirectories
        if artist_base_dir:
            for entry in os.listdir(artist_base_dir):
                entry_path = os.path.join(artist_base_dir, entry)
                if os.path.isdir(entry_path):
                    albums.append(entry)

        return albums

    @staticmethod
    def _album_exists(title: str, existing_names: List[str]) -> bool:
        """Check if an album title matches any existing local directory name."""
        title_lower = title.lower()
        # Normalize: remove punctuation and extra spaces
        title_norm = re.sub(r'[^\w\s]', '', title_lower).strip()
        title_words = set(title_norm.split())

        for name in existing_names:
            name_lower = name.lower()
            name_norm = re.sub(r'[^\w\s]', '', name_lower).strip()
            name_words = set(name_norm.split())

            # If most words overlap, it's a match
            if title_words and name_words:
                overlap = title_words & name_words
                if len(overlap) >= min(len(title_words), len(name_words)) * 0.6:
                    return True

        return False
