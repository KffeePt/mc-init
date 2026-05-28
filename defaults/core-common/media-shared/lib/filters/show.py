"""Show filter — identifies TV show/episode/season torrents."""

import re
from .base import BaseFilter


class ShowFilter(BaseFilter):
    """Filter for TV show-type torrents (episodes, seasons, bundles)."""

    _TV_PATTERNS = [
        r'S\d{2}E\d{2}',                    # S01E01
        r'Season\s*\d+',                     # Season 1, Season 01
        r'S\d{2}\s*[-–]\s*S?\d{2}',          # S01-S05
        r'COMPLETE\s+(SEASON|SERIES)',        # COMPLETE SEASON
        r'E\d{2}\b(?![-–])',                 # E01 (not followed by range)
        r'\bE\d{2}\s*[-–]\s*E\d{2}',         # E01-E12
    ]

    @property
    def media_type(self) -> str:
        return "show"

    def is_match(self, name: str) -> bool:
        for pat in self._TV_PATTERNS:
            if re.search(pat, name, re.I):
                return True
        return False
