"""Gap analysis package — compare local library against external databases."""

from .base import BaseGapAnalyzer, GapResult
from .show import ShowGapAnalyzer
from .music import MusicGapAnalyzer
from .movie import MovieGapAnalyzer

_REGISTRY = {
    "show": ShowGapAnalyzer,
    "music": MusicGapAnalyzer,
    "movie": MovieGapAnalyzer,
}


def get_analyzer(media_type: str) -> BaseGapAnalyzer:
    """Get the gap analyzer for a media type."""
    cls = _REGISTRY.get(media_type)
    if cls:
        return cls()
    raise ValueError("Unknown media type: " + media_type)


__all__ = [
    "BaseGapAnalyzer", "GapResult",
    "ShowGapAnalyzer", "MusicGapAnalyzer", "MovieGapAnalyzer",
    "get_analyzer",
]
