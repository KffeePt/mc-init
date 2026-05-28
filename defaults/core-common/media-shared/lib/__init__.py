"""Media search library — modular torrent search, download, and scanning toolkit.

Packages:
    search      — Torrent indexers (BitSearch, YTS, apibay) and SearchEngine
    filters     — Media type classifiers (movie, show, music)
    metadata    — Metadata extractors and trust classification
    qbittorrent — qBittorrent API client (PowerShell bridge for WSL)
    scanner     — Malware scanner (extension check, metadata, Defender)
    formatters  — Terminal display formatters
"""

from .search import SearchEngine
from .qbittorrent import QBittorrentClient
from .scanner import MalwareScanner
from .gap import get_analyzer, GapResult
from .formatters import ResultFormatter, StatusFormatter, ScanFormatter, GapFormatter

__all__ = [
    "SearchEngine",
    "QBittorrentClient",
    "MalwareScanner",
    "get_analyzer", "GapResult",
    "ResultFormatter",
    "StatusFormatter",
    "ScanFormatter",
    "GapFormatter",
]
