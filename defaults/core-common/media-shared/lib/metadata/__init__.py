"""Metadata package — extractors and trust classification."""

from .extractors import (
    extract_resolution,
    extract_format,
    extract_codec,
    extract_audio_quality,
    extract_release_group,
)
from .trust import TrustClassifier

__all__ = [
    "extract_resolution",
    "extract_format",
    "extract_codec",
    "extract_audio_quality",
    "extract_release_group",
    "TrustClassifier",
]
