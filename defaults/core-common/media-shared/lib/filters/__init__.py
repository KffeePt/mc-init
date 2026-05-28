"""Filters package — media type classification."""

from typing import Optional
from .base import BaseFilter
from .movie import MovieFilter
from .show import ShowFilter
from .music import MusicFilter

_REGISTRY: dict[str, BaseFilter] = {
    "movie": MovieFilter(),
    "show": ShowFilter(),
    "music": MusicFilter(),
}


def get_filter(media_type: str) -> Optional[BaseFilter]:
    """Get the filter instance for a media type, or None."""
    return _REGISTRY.get(media_type)


__all__ = ["BaseFilter", "MovieFilter", "ShowFilter", "MusicFilter", "get_filter"]
