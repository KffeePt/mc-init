"""Movie gap analyzer — detect sequels and related movies via Cinemagoer (IMDBPY).

Uses the IMDB database to find:
  - Sequels and prequels
  - Movies in the same franchise/series
  - Related titles
"""

import os
import re
from typing import Dict, Any, List, Optional

from .base import BaseGapAnalyzer, GapResult


class MovieGapAnalyzer(BaseGapAnalyzer):
    """Analyze gaps in a movie library by detecting sequels and franchise entries."""

    DEFAULT_LIBRARY_PATH = "/mnt/d/Movies/"

    def analyze(self, query: str, library_path: Optional[str] = None) -> GapResult:
        result = GapResult(media_type="movie", query=query)

        # 1. Search for movie on IMDB
        movie = self._find_movie(query)
        if not movie:
            result.metadata["error"] = "Movie not found on IMDB"
            return result

        movie_id = movie.movieID
        title = movie.get("title", query)
        year = movie.get("year", "")
        result.source = "IMDB (Cinemagoer)"
        result.metadata["movie_title"] = title
        result.metadata["movie_year"] = year
        result.metadata["movie_id"] = movie_id

        # 2. Find sequels/prequels/related
        related = self._find_related(movie)

        # The main movie counts too
        main_entry = {
            "title": title,
            "year": year,
            "id": movie_id,
            "kind": "original",
        }
        all_entries = [main_entry] + related
        result.total_expected = len(all_entries)

        # 3. Scan local library
        lib_path = library_path or self.DEFAULT_LIBRARY_PATH
        existing_names = self._scan_local_movies(lib_path)

        # 4. Classify
        for entry in all_entries:
            if self._movie_exists(entry["title"], entry.get("year", ""), existing_names):
                result.existing.append(entry)
            else:
                result.missing.append(entry)

        return result

    def search_missing(self, gap_result: GapResult) -> Dict[str, Any]:
        """Search for missing sequels/movies on torrent indexers."""
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from lib.search import SearchEngine

        engine = SearchEngine()
        search_results = {}

        for item in gap_result.missing:
            title = item["title"]
            year = item.get("year", "")
            query = title
            if year:
                query += " " + str(year)

            data = engine.search(query, media_type="movie", limit=5)
            search_results[title] = data

        return search_results

    def _find_movie(self, query: str):
        """Search IMDB for a movie. Returns cinemagoer Movie object or None."""
        try:
            from imdb import Cinemagoer
            ia = Cinemagoer()
            results = ia.search_movie(query)
            # Find first movie (not TV show, not game)
            for r in results:
                if r.get("kind") in ("movie",):
                    return r
            # Fallback: return first result
            if results:
                return results[0]
        except Exception:
            pass

        # Fallback: construct a minimal movie dict from the query
        # This allows sequel detection even when Cinemagoer fails
        return type('Movie', (), {
            'movieID': '0',
            'get': lambda self, key, default='': query if key == 'title' else default,
            '__getitem__': lambda self, key: query if key == 'title' else '',
        })()

    def _find_related(self, movie) -> List[Dict]:
        """Find sequels, prequels, and franchise entries for a movie."""
        related = []
        title = movie.get("title", "") if hasattr(movie, 'get') else str(movie)
        movie_id = movie.movieID if hasattr(movie, 'movieID') else None

        # Try Cinemagoer first (if it worked)
        if movie_id and movie_id != '0':
            try:
                from imdb import Cinemagoer
                ia = Cinemagoer()
                full_movie = ia.get_movie(movie_id)

                if "sequels" in full_movie:
                    for sequel in full_movie["sequels"]:
                        related.append({
                            "title": sequel.get("title", "Unknown"),
                            "year": sequel.get("year", ""),
                            "id": sequel.movieID,
                            "kind": "sequel",
                        })

                if "follows" in full_movie:
                    for prequel in full_movie["follows"]:
                        related.append({
                            "title": prequel.get("title", "Unknown"),
                            "year": prequel.get("year", ""),
                            "id": prequel.movieID,
                            "kind": "prequel",
                        })
            except Exception:
                pass

        # If no IMDB connections found, use title-based sequel detection
        if not related and title:
            related = self._detect_sequels_by_title(title)

        # Also search using TVmaze as additional source for movie franchises
        if not related and title:
            tvmaze_related = self._search_tvmaze_for_franchise(title)
            related.extend(tvmaze_related)

        return related

    @staticmethod
    def _detect_sequels_by_title(title: str) -> List[Dict]:
        """Heuristic: detect numbered sequels from the title and generate expected entries.

        E.g. "Insidious" → check for "Insidious 2", "Insidious 3", etc.
        """
        related = []
        # Check if title ends with a number (it's already a sequel)
        base_match = re.match(r'(.+?)\s+(\d+)$', title)

        # Try to find common sequel patterns for up to 6 entries
        if base_match:
            base_name = base_match.group(1).strip()
            current_num = int(base_match.group(2))
        else:
            base_name = title
            current_num = 1

        # Generate expected sequel entries
        for n in range(1, 7):
            if n == current_num:
                continue
            sequel_title = base_name + " " + str(n)
            related.append({
                "title": sequel_title,
                "year": "",
                "id": "",
                "kind": "possible sequel",
            })

        return related

    def _search_tvmaze_for_franchise(self, title: str) -> List[Dict]:
        """Fallback: search TVmaze for shows/movies with similar names (franchise detection)."""
        import urllib.parse
        related = []
        encoded = urllib.parse.quote(title, safe="")
        url = "https://api.tvmaze.com/search/shows?q=" + encoded

        data = self._fetch_json(url)
        if not data or not isinstance(data, list):
            return related

        # Look for entries that share the base name (e.g. "Insidious", "Insidious: The Red Door")
        title_lower = title.lower()
        title_words = set(title_lower.split()) - {"the", "a", "an"}

        for entry in data[:10]:
            show = entry.get("show", {})
            show_name = show.get("name", "")
            show_lower = show_name.lower()
            show_words = set(show_lower.split()) - {"the", "a", "an"}

            # Must share most words with original title but not be identical
            if show_lower != title_lower:
                overlap = title_words & show_words
                if len(overlap) >= len(title_words) * 0.6:
                    related.append({
                        "title": show_name,
                        "year": show.get("premiered", "")[:4] if show.get("premiered") else "",
                        "id": show.get("id", ""),
                        "kind": "franchise entry",
                    })

        return related

    def _scan_local_movies(self, library_path: str) -> List[str]:
        """Scan local filesystem for existing movies. Returns list of directory/file names."""
        movies = []
        if not os.path.exists(library_path):
            return movies

        for entry in os.listdir(library_path):
            movies.append(entry)

        return movies

    @staticmethod
    def _movie_exists(title: str, year: str, existing_names: List[str]) -> bool:
        """Check if a movie title matches any existing local entry."""
        title_lower = title.lower()
        title_norm = re.sub(r'[^\w\s]', '', title_lower).strip()
        title_words = set(title_norm.split()) - {"the", "a", "an", "of", "and"}

        for name in existing_names:
            name_lower = name.lower()
            name_norm = re.sub(r'[^\w\s]', '', name_lower).strip()
            name_words = set(name_norm.split()) - {"the", "a", "an", "of", "and"}

            if not title_words or not name_words:
                continue

            overlap = title_words & name_words
            # Need at least 60% word overlap
            if len(overlap) >= max(len(title_words), len(name_words)) * 0.6:
                # Also check year if provided
                if year and str(year) in name:
                    return True
                elif not year:
                    return True

        return False
