"""Base filter interface — all media type filters inherit from this."""

from abc import ABC, abstractmethod


class BaseFilter(ABC):
    """Abstract base class for media type filters."""

    @abstractmethod
    def is_match(self, name: str) -> bool:
        """Return True if the torrent name matches this media type."""
        ...

    @property
    @abstractmethod
    def media_type(self) -> str:
        """Human-readable media type name."""
        ...
