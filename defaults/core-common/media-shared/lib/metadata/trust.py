"""Trust classifier — rates torrent result trustworthiness."""

import re
from .extractors import extract_release_group


class TrustClassifier:
    """Classifies torrent trust level based on release group, uploader, and swarm health."""

    KNOWN_SAFE_GROUPS = {
        'YTS', 'YIFY', 'RARBG', 'GalaxyRG', 'SPARKS', 'Framestor', 'FraMeSToR',
        'RMTeam', 'NTb', 'FLUX', 'SiGMA', 'ETHEL', 'MEGusta', 'EDITH', 'GRACE',
        'BiOMA', 'RAWR', 'AMB3R', 'HiQVE', 'PSA', 'Kitsune', 'Silence', 'Panda',
        't3nzin', 'Garshasp', 'afm72', 'Ghost', 'BONE', 'SARTRE', 'HETeam',
        'maximersk', 'i_c', 'LAMA', 'WORLD', 'LOOTera', 'OFT', 'REKoDE', 'EVO',
        'Ozlem', 'HANDJOB', 'Devil', 'AFG', 'NGP', 'CAKES', 'SuccessfulCrab',
        'ELiTE', 'REVILS', 'higgsboson', 'playWEB', 'PCOK', 'nikt0', 'iFT',
        'AMORT', 'TGx', 'eztv', 'TORRENTGALAXY', 'JFF', 'mSD', 'FQM', '0TV',
        # Music-specific groups
        'DHV', 'FID', 'DRS', 'MTC', 'Qobuz', 'Deezer', 'TIDAL', 'Beatport',
    }

    SUSPICIOUS_KEYWORDS = [
        'exe', 'iso', 'installer', 'keygen', 'serial',
        'free download', 'no survey', 'cracked', 'hack',
    ]

    def classify(self, result: dict) -> tuple:
        """Classify trust level. Returns (level_name, emoji) tuple.

        Levels: TRUSTED, KNOWN, VERIFIED, ACCEPTABLE, LOW, RISKY
        """
        name = result.get("name", "").upper()
        seeders = result.get("seeders", 0)
        leechers = result.get("leechers", 0)
        uploader_status = result.get("uploader_status", "")

        # Suspicious keywords → RISKY
        for kw in self.SUSPICIOUS_KEYWORDS:
            if kw.upper() in name:
                return "RISKY", "🔴"

        # Known safe group → TRUSTED
        group = extract_release_group(result.get("name", ""))
        if group in self.KNOWN_SAFE_GROUPS:
            return "TRUSTED", "🟢"

        # Uploader status
        if uploader_status in ("vip", "moderator"):
            return "TRUSTED", "🟢"
        if uploader_status in ("trusted", "helper"):
            return "KNOWN", "🟡"

        # Swarm health heuristic
        if seeders > 50 and (leechers == 0 or seeders / max(leechers, 1) > 5):
            return "VERIFIED", "🟢"
        if seeders > 10:
            return "ACCEPTABLE", "🟠"
        if seeders > 0:
            return "LOW", "🟠"

        return "RISKY", "🔴"
