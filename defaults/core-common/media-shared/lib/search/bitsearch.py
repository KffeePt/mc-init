"""BitSearch.to searcher — primary source, HTML-based, no Cloudflare."""

import re
import html as html_lib
import urllib.parse
from typing import Dict, Any, Optional

from .base import BaseSearcher


class BitSearchSearcher(BaseSearcher):
    """Search BitSearch.to via HTML scraping."""

    @property
    def source_name(self) -> str:
        return "BitSearch.to"

    def search(self, query: str, limit: int = 30, **kwargs) -> Dict[str, Any]:
        encoded_q = urllib.parse.quote(query, safe="+")
        url = f"https://bitsearch.to/search?q={encoded_q}"

        raw = self._fetch_url(url)
        if raw is None:
            return {"source": self.source_name, "error": "Failed to fetch", "results": []}

        decoded = html_lib.unescape(raw)
        return self._parse_results(decoded, limit)

    def _parse_results(self, html: str, limit: int) -> Dict[str, Any]:
        dl_pattern = re.compile(
            r'/download/torrent/([a-fA-F0-9]{40})\?title=([^"&]+)',
            re.IGNORECASE,
        )

        entries = dl_pattern.findall(html)
        seen = set()
        results = []

        for info_hash, name_encoded in entries:
            info_hash = info_hash.upper()
            if info_hash in seen:
                continue
            seen.add(info_hash)

            name = name_encoded.replace("+", " ")
            block = self._extract_block(html, info_hash)

            size = self._extract_size(block)
            seeders = self._extract_seeders(block)
            leechers = self._extract_leechers(block)
            date = self._extract_date(block)
            magnet = self._build_magnet(info_hash, name)

            results.append({
                "name": name,
                "size": size,
                "date": date,
                "seeders": seeders,
                "leechers": leechers,
                "info_hash": info_hash,
                "magnet": magnet,
                "source": self.source_name,
            })

        results.sort(key=lambda x: x["seeders"], reverse=True)
        return {"source": self.source_name, "results": results[:limit]}

    @staticmethod
    def _extract_block(html: str, info_hash: str) -> str:
        pos = html.find(info_hash)
        if pos < 0:
            return ""
        return html[max(0, pos - 2500):pos + 500]

    @staticmethod
    def _extract_size(block: str) -> str:
        m = re.search(r'fa-download[^>]*>\s*</i>\s*<span>([^<]+)</span>', block)
        return m.group(1).strip() if m else "Unknown"

    @staticmethod
    def _extract_seeders(block: str) -> int:
        m = re.search(r'fa-arrow-up[^>]*>\s*</i>\s*<span[^>]*>(\d+)</span>', block)
        return int(m.group(1)) if m else 0

    @staticmethod
    def _extract_leechers(block: str) -> int:
        m = re.search(r'fa-arrow-down[^>]*>\s*</i>\s*<span[^>]*>(\d+)</span>', block)
        return int(m.group(1)) if m else 0

    @staticmethod
    def _extract_date(block: str) -> str:
        m = re.search(r'fa-calendar[^>]*>\s*</i>\s*<span>([^<]+)</span>', block)
        return m.group(1).strip() if m else "Unknown"
