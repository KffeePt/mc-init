"""Base gap analyzer interface — all gap analyzers inherit from this."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class GapResult:
    """Represents a gap analysis result — what you have vs what's missing."""

    def __init__(self, media_type: str, query: str):
        self.media_type = media_type
        self.query = query
        self.existing: List[Dict[str, Any]] = []
        self.missing: List[Dict[str, Any]] = []
        self.total_expected: int = 0
        self.source: str = ""
        self.metadata: Dict[str, Any] = {}

    @property
    def completion_pct(self) -> float:
        if self.total_expected == 0:
            return 0.0
        return len(self.existing) / self.total_expected * 100

    @property
    def is_complete(self) -> bool:
        return len(self.missing) == 0 and self.total_expected > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "media_type": self.media_type,
            "query": self.query,
            "source": self.source,
            "total_expected": self.total_expected,
            "existing_count": len(self.existing),
            "missing_count": len(self.missing),
            "completion_pct": round(self.completion_pct, 1),
            "is_complete": self.is_complete,
            "existing": self.existing,
            "missing": self.missing,
            "metadata": self.metadata,
        }


class BaseGapAnalyzer(ABC):
    """Abstract base class for gap analysis — compare local library against known databases."""

    @abstractmethod
    def analyze(self, query: str, library_path: Optional[str] = None) -> GapResult:
        """Analyze gaps between local library and external database.

        Args:
            query: Show/artist/movie name to look up
            library_path: Override default library path

        Returns:
            GapResult with existing and missing items
        """
        ...

    @abstractmethod
    def search_missing(self, gap_result: GapResult) -> Dict[str, Any]:
        """Search for missing items on torrent indexers.

        Args:
            gap_result: A GapResult from analyze() with missing items

        Returns:
            Dict mapping missing item identifiers to search results
        """
        ...

    @staticmethod
    def _fetch_json(url: str, headers: Optional[dict] = None, timeout: int = 15) -> Optional[Any]:
        """Fetch URL and parse JSON response."""
        import json
        import urllib.request

        default_headers = {"User-Agent": "HermesMediaSearch/1.0"}
        if headers:
            default_headers.update(headers)

        req = urllib.request.Request(url, headers=default_headers)
        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
            raw = resp.read().decode("utf-8", errors="ignore")
            return json.loads(raw)
        except Exception:
            return None
