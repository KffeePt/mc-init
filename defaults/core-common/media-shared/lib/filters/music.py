"""Music filter — identifies music album/discography/single torrents."""

import re
from .base import BaseFilter


class MusicFilter(BaseFilter):
    """Filter for music-type torrents (albums, discographies, singles, OSTs)."""

    _EXCLUDE_PATTERNS = [
        # TV patterns
        r'S\d{2}E\d{2}', r'Season\s*\d+', r'COMPLETE\s+(SEASON|SERIES)',
        # Game signals
        r'\bFitGirl\b', r'\bCODEX\b', r'\bRELOADED\b', r'\bRUNE\b', r'\bRepack\b',
        # Porn
        r'\bXXX\b', r'\bPorn\b', r'\bBrazzers\b',
    ]

    _QUALITY_SIGNALS = [
        r'\bFLAC\b', r'\bMP3\b', r'\bAAC\b', r'\bALAC\b', r'\bOPUS\b',
        r'\b320kbps\b', r'\b256kbps\b', r'\b192kbps\b', r'\bV0\b', r'\bV2\b',
        r'\bLossless\b', r'\bHi-Res\b', r'\b24bit\b', r'\b16bit\b',
        r'\b24-96\b', r'\b24-44\b', r'\b24-48\b', r'\b96kHz\b', r'\b44\.1kHz\b',
        r'\bCUE\b', r'\bLOG\b', r'\bSCANS\b',
    ]

    _CONTENT_SIGNALS = [
        r'\bAlbum\b', r'\bDiscography\b', r'\bDiscog\b',
        r'\bOST\b', r'\bSoundtrack\b', r'\bScore\b',
        r'\bVinyl\b', r'\bLP\b', r'\bEP\b', r'\bSingle\b',
        r'\bDeluxe\b', r'\bRemaster\w*\b',
        r'\bB-Sides\b', r'\bLive\s+(Album|Concert)\b',
        r'\bCD\b', r'\bWEB\b',
    ]

    @property
    def media_type(self) -> str:
        return "music"

    def is_match(self, name: str) -> bool:
        # Exclude non-music first
        for pat in self._EXCLUDE_PATTERNS:
            if re.search(pat, name, re.I):
                return False

        # Check quality signals
        for pat in self._QUALITY_SIGNALS:
            if re.search(pat, name, re.I):
                return True

        # Check content type signals
        for pat in self._CONTENT_SIGNALS:
            if re.search(pat, name, re.I):
                return True

        # Pattern: Artist-Album-Year (common in music torrents)
        if re.search(r'[A-Z][a-z]+-[A-Z][a-z]+.*(19|20)\d{2}', name):
            return True

        # Audio file extensions in name
        audio_exts = [r'\.mp3\b', r'\.flac\b', r'\.m4a\b', r'\.aac\b', r'\.ogg\b', r'\.opus\b', r'\.wav\b']
        for ext in audio_exts:
            if re.search(ext, name, re.I):
                return True

        return False
