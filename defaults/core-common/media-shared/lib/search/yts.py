"""YTS.ag searcher — movie enrichment source with verified releases."""

import json
import urllib.parse
from typing import Dict, Any

from .base import BaseSearcher


class YTSSearcher(BaseSearcher):
    """Search YTS.ag API for verified movie releases."""

    @property
    def source_name(self) -> str:
        return "YTS.ag"

    def search(self, query: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        encoded_q = urllib.parse.quote(query, safe="")
        url = f"https://yts.ag/api/v2/list_movies.json?query_term={encoded_q}&limit={limit}"

        raw = self._fetch_url(url)
        if raw is None:
            return {"source": self.source_name, "error": "Failed to fetch", "results": []}

        return self._parse_response(raw, limit)

    def _parse_response(self, raw_json: str, limit: int) -> Dict[str, Any]:
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            return {"source": self.source_name, "error": "Invalid JSON", "results": []}

        if data.get("status") != "ok":
            return {"source": self.source_name, "results": []}

        movie_count = data.get("data", {}).get("movie_count", 0)
        if movie_count == 0:
            return {"source": self.source_name, "results": []}

        results = []
        for movie in data.get("data", {}).get("movies", []):
            for torrent in movie.get("torrents", []):
                info_hash = torrent.get("hash", "").upper()
                name = f"{movie['title']} ({movie['year']}) [{torrent['quality']}] [{torrent['type']}]"
                magnet = self._build_magnet(info_hash, name) if info_hash else ""

                results.append({
                    "name": name,
                    "size": torrent.get("size", "Unknown"),
                    "date": str(movie.get("year", "Unknown")),
                    "seeders": int(torrent.get("seeds", 0)),
                    "leechers": int(torrent.get("peers", 0)),
                    "info_hash": info_hash,
                    "magnet": magnet,
                    "source": self.source_name,
                    "imdb": movie.get("imdb_code", ""),
                    "rating": movie.get("rating", ""),
                    "yts_quality": torrent.get("quality", ""),
                    "yts_type": torrent.get("type", ""),
                })

        results.sort(key=lambda x: x["seeders"], reverse=True)
        return {"source": self.source_name, "results": results[:limit]}
