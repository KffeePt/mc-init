"""apibay.org searcher — Pirate Bay API fallback."""

import json
import re
import urllib.parse
from typing import Dict, Any

from .base import BaseSearcher


class ApiBaySearcher(BaseSearcher):
    """Search apibay.org (Pirate Bay API). Category filtering is unreliable."""

    @property
    def source_name(self) -> str:
        return "apibay.org"

    def search(self, query: str, limit: int = 30, cat: int = 0, **kwargs) -> Dict[str, Any]:
        encoded_q = urllib.parse.quote(query, safe="")
        url = f"https://apibay.org/q.php?q={encoded_q}&cat={cat}"

        headers = {"Referer": "https://thepiratebay.org/"}
        raw = self._fetch_url(url, headers=headers)
        if raw is None:
            return {"source": self.source_name, "error": "Failed to fetch", "results": []}

        return self._parse_response(raw, limit)

    def _parse_response(self, raw_json: str, limit: int) -> Dict[str, Any]:
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            return {"source": self.source_name, "error": "Invalid JSON", "results": []}

        # "No results" placeholder
        if isinstance(data, list) and len(data) == 1 and data[0].get("id") == "0":
            return {"source": self.source_name, "results": []}

        results = []
        for item in data[:limit * 3]:
            size_bytes = int(item.get("size", 0))
            size = self._format_size(size_bytes)
            info_hash = item.get("info_hash", "").upper()
            name = item.get("name", "Unknown")
            magnet = self._build_magnet(info_hash, name) if info_hash else ""

            results.append({
                "name": name,
                "size": size,
                "date": str(item.get("added", "Unknown")),
                "seeders": int(item.get("seeders", 0)),
                "leechers": int(item.get("leechers", 0)),
                "info_hash": info_hash,
                "magnet": magnet,
                "source": self.source_name,
                "uploader": item.get("username", ""),
                "uploader_status": item.get("status", ""),
                "category": item.get("category", ""),
                "imdb": item.get("imdb", ""),
            })

        results.sort(key=lambda x: x["seeders"], reverse=True)
        return {"source": self.source_name, "results": results[:limit]}

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes <= 0:
            return "Unknown"
        if size_bytes >= 1024 ** 3:
            return f"{size_bytes / (1024 ** 3):.2f} GiB"
        if size_bytes >= 1024 ** 2:
            return f"{size_bytes / (1024 ** 2):.1f} MiB"
        return f"{size_bytes / 1024:.0f} KiB"
