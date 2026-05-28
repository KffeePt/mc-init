"""Base searcher interface — all indexers inherit from this."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseSearcher(ABC):
    """Abstract base class for torrent search sources."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable source name (e.g. 'BitSearch.to')."""
        ...

    @abstractmethod
    def search(self, query: str, limit: int = 30, **kwargs) -> Dict[str, Any]:
        """Execute a search and return structured results.

        Returns:
            {
                "source": self.source_name,
                "results": [
                    {
                        "name": str,
                        "size": str,
                        "date": str,
                        "seeders": int,
                        "leechers": int,
                        "info_hash": str,
                        "magnet": str,
                        "source": str,
                        # Optional fields per source:
                        "uploader": str,
                        "uploader_status": str,
                        ...
                    }
                ],
                "error": Optional[str]  # present only on failure
            }
        """
        ...

    def _build_magnet(self, info_hash: str, display_name: str) -> str:
        """Construct a magnet URI with standard tracker list."""
        trackers = [
            "udp://tracker.opentrackr.org:1337/announce",
            "udp://open.stealth.si:80/announce",
            "udp://tracker.torrent.eu.org:451/announce",
            "udp://exodus.desync.com:6969/announce",
            "udp://tracker.dler.org:6969/announce",
            "udp://tracker.breizh.pm:6969/announce",
        ]
        import urllib.parse
        tr = "&tr=".join(urllib.parse.quote(t) for t in trackers)
        dn = urllib.parse.quote(display_name)
        return f"magnet:?xt=urn:btih:{info_hash}&dn={dn}&tr={tr}"

    def _fetch_url(self, url: str, headers: Optional[dict] = None, timeout: int = 15) -> Optional[str]:
        """Fetch a URL and return decoded text, or None on error."""
        import urllib.request
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        if headers:
            default_headers.update(headers)
        req = urllib.request.Request(url, headers=default_headers)
        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
            return resp.read().decode("utf-8", errors="ignore")
        except Exception:
            return None
