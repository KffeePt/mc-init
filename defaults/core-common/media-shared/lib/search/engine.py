"""Search engine — orchestrates multiple searchers, deduplicates, and sorts results."""

import re
from typing import Dict, Any, List, Optional

from .base import BaseSearcher
from .bitsearch import BitSearchSearcher
from .yts import YTSSearcher
from .apibay import ApiBaySearcher
from ..filters import get_filter
from ..metadata.extractors import extract_resolution, extract_audio_quality


class SearchEngine:
    """Orchestrates searches across multiple sources, applies filters, deduplicates."""

    def __init__(self, searchers: Optional[List[BaseSearcher]] = None):
        self.searchers = searchers or [
            BitSearchSearcher(),
            ApiBaySearcher(),
        ]
        self._yts = YTSSearcher()

    def search(self, query: str, media_type: str = "movie", limit: int = 20) -> Dict[str, Any]:
        """Search all sources, filter by media type, deduplicate, sort.

        Args:
            query: Search string
            media_type: 'movie', 'show', or 'music'
            limit: Maximum results to return

        Returns:
            {
                "query": str,
                "type": str,
                "total_sources": int,
                "errors": list,
                "results": list
            }
        """
        all_results: List[Dict] = []
        errors: List[str] = []

        # BitSearch + apibay (always)
        for searcher in self.searchers:
            result = searcher.search(query, limit=limit * 2)
            if result.get("error"):
                errors.append(f"{searcher.source_name}: {result['error']}")
            else:
                all_results.extend(result["results"])

        # YTS (movie-only enrichment)
        if media_type == "movie":
            yts_result = self._yts.search(query, limit=limit)
            if yts_result.get("error"):
                errors.append(f"YTS: {yts_result['error']}")
            else:
                all_results.extend(yts_result["results"])

        # Apply media type filter
        media_filter = get_filter(media_type)
        if media_filter:
            all_results = [r for r in all_results if media_filter.is_match(r.get("name", ""))]

        # Deduplicate by info_hash (keep highest-seeder version)
        deduped = self._deduplicate(all_results)

        # Sort by media-type-appropriate strategy
        deduped = self._sort(deduped, media_type)

        total_sources = (len(self.searchers) + (1 if media_type == "movie" else 0)) - len(errors)

        return {
            "query": query,
            "type": media_type,
            "total_sources": total_sources,
            "errors": errors,
            "results": deduped[:limit],
        }

    @staticmethod
    def _deduplicate(results: List[Dict]) -> List[Dict]:
        seen: Dict[str, Dict] = {}
        for r in results:
            h = r.get("info_hash", "")
            if not h:
                continue
            if h not in seen or r["seeders"] > seen[h]["seeders"]:
                seen[h] = r
        return list(seen.values())

    @staticmethod
    def _sort(results: List[Dict], media_type: str) -> List[Dict]:
        if media_type == "music":
            results.sort(key=SearchEngine._music_sort_key)
        else:
            results.sort(key=SearchEngine._video_sort_key)
        return results

    @staticmethod
    def _video_sort_key(r: Dict) -> tuple:
        """Sort: 1080p first, then highest resolution, then lowest size, then seeders."""
        res = extract_resolution(r.get("name", ""))
        res_score = {"1080p": 100, "4K": 90, "720p": 70, "480p": 40, "Unknown": 20}.get(res, 20)
        size_val = SearchEngine._parse_size(r.get("size", "0"))
        return (-res_score, size_val, -r.get("seeders", 0))

    @staticmethod
    def _music_sort_key(r: Dict) -> tuple:
        """Sort: FLAC first, then highest quality, then lowest size, then seeders."""
        quality = extract_audio_quality(r.get("name", ""))
        quality_score = {
            "Hi-Res": 120, "24-bit": 110, "FLAC": 100, "ALAC": 95,
            "Lossless": 90, "320kbps": 80, "256kbps": 60,
            "192kbps": 40, "AAC": 35, "Opus": 30, "MP3": 20,
            "Unknown": 10,
        }.get(quality, 10)
        size_val = SearchEngine._parse_size(r.get("size", "0"))
        return (-quality_score, size_val, -r.get("seeders", 0))

    @staticmethod
    def _parse_size(size_str: str) -> float:
        try:
            val = float(re.match(r'([\d.]+)', size_str).group(1))
            if 'GiB' in size_str or 'GB' in size_str:
                val *= 1024
            elif 'TB' in size_str or 'TiB' in size_str:
                val *= 1024 * 1024
            return val
        except (AttributeError, ValueError):
            return 0.0
