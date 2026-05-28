"""Movie filter — identifies movie torrents, excludes TV, games, and porn."""

import re
from .base import BaseFilter


class MovieFilter(BaseFilter):
    """Filter for movie-type torrents."""

    # Patterns that indicate this is NOT a movie
    _GAME_SIGNALS = [
        r'\bPC\s*(Game|GAME)\b', r'\bFitGirl\b', r'\bCODEX\b', r'\bRELOADED\b',
        r'\bRUNE\b', r'\bIgruha\b', r'\bDODI\b', r'\bRepack\b',
        r'\bv\d+\.\d+\.\d+\b', r'\bUpdate\s+v\b',
    ]

    _PORN_SIGNALS = [
        r'\bXXX\b', r'\bPorn\b', r'\bPORN\b', r'\bSex\b', r'\bAnal\b',
        r'\bPussy\b', r'\bDick\b', r'\bFuck\b', r'\bCum\b', r'\bMilf\b',
        r'\bDevilsFilm\b', r'\bBrazzers\b', r'\bBangBros\b', r'\bNaughty\b',
        r'\bPack Movies\b.*\bWEB-',
    ]

    _TV_PATTERNS = [
        r'S\d{2}E\d{2}',
        r'Season\s*\d+',
        r'S\d{2}\s*[-–]\s*S?\d{2}',
        r'COMPLETE\s+(SEASON|SERIES)',
        r'E\d{2}\b(?![-–])',
        r'\bE\d{2}\s*[-–]\s*E\d{2}',
    ]

    @property
    def media_type(self) -> str:
        return "movie"

    def is_match(self, name: str) -> bool:
        # Exclude games
        for pat in self._GAME_SIGNALS:
            if re.search(pat, name, re.I):
                return False
        # Exclude porn
        for pat in self._PORN_SIGNALS:
            if re.search(pat, name, re.I):
                return False
        # Exclude TV patterns
        for pat in self._TV_PATTERNS:
            if re.search(pat, name, re.I):
                return False
        return True
