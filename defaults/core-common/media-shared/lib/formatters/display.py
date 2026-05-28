"""Formatters — display formatting for search results, download status, and scan results."""

from ..metadata.extractors import (
    extract_resolution, extract_format, extract_codec,
    extract_audio_quality, extract_release_group,
)
from ..metadata.trust import TrustClassifier


class ResultFormatter:
    """Format search results for terminal display."""

    EMOJI_MAP = {
        "movie": "🎬",
        "show": "📺",
        "music": "🎵",
    }

    def __init__(self):
        self._trust = TrustClassifier()

    def format(self, data: dict, media_type: str = "movie") -> str:
        """Format search results for display."""
        results = data.get("results", [])
        if not results:
            query = data.get("query", "?")
            errors = data.get("errors", [])
            return f"No results found for '{query}' [{media_type}]\nErrors: {errors}"

        lines = []
        emoji = self.EMOJI_MAP.get(media_type, "🔍")
        query = data.get("query", "?")
        total_sources = data.get("total_sources", 0)

        lines.append(emoji + " " + query + " — Search Results")
        lines.append("Sources: " + str(total_sources) + "/3 active | " + str(len(results)) + " results\n")

        if media_type == "music":
            self._format_music(results, lines)
        else:
            self._format_video(results, lines)

        return "\n".join(lines)

    def _format_video(self, results: list, lines: list):
        for i, r in enumerate(results[:20], 1):
            res = extract_resolution(r["name"])
            fmt = extract_format(r["name"])
            codec = extract_codec(r["name"])
            trust, emoji_t = self._trust.classify(r)
            group = extract_release_group(r["name"])

            parts = [res]
            if fmt != "Unknown":
                parts.append(fmt)
            if codec != "Unknown":
                parts.append(codec)
            tech = " | ".join(parts) if parts else "Unknown quality"

            source_tag = "[" + r.get("source", "?") + "]"
            group_tag = " | " + group if group else ""

            lines.append("  " + str(i) + ". " + emoji_t + " " + r["name"][:72])
            lines.append("     " + tech + " | " + r["size"] + " | S:" + str(r["seeders"]) + " L:" + str(r["leechers"]) + " | " + source_tag + group_tag)
            lines.append("")

    def _format_music(self, results: list, lines: list):
        for i, r in enumerate(results[:20], 1):
            quality = extract_audio_quality(r["name"])
            trust, emoji_t = self._trust.classify(r)
            group = extract_release_group(r["name"])

            source_tag = "[" + r.get("source", "?") + "]"
            group_tag = " | " + group if group else ""

            lines.append("  " + str(i) + ". " + emoji_t + " " + r["name"][:72])
            lines.append("     " + quality + " | " + r["size"] + " | S:" + str(r["seeders"]) + " L:" + str(r["leechers"]) + " | " + source_tag + group_tag)
            lines.append("")


class StatusFormatter:
    """Format download status for terminal display."""

    def format(self, data: dict) -> str:
        if data.get("status") == "error":
            return "❌ " + data["message"]

        torrents = data.get("torrents", [])
        if not torrents:
            return "📭 No active downloads"

        lines = ["📥 qBittorrent — Download Status\n"]

        for i, t in enumerate(torrents, 1):
            lines.append("  " + str(i) + ". " + t["status"] + " " + t["name"][:65])
            lines.append(
                "     " + t["progress"] + " | " + t["size"] +
                " | ⬇" + t["download_speed"] + " ⬆" + t["upload_speed"] +
                " | ETA: " + t["eta"] +
                " | S:" + str(t["seeds"]) + " P:" + str(t["peers"])
            )
            lines.append("")

        active = [t for t in torrents if "Downloading" in t["status"]]
        complete = [t for t in torrents if "Complete" in t["status"]]
        lines.append("  Active: " + str(len(active)) + " | Complete: " + str(len(complete)) + " | Total: " + str(len(torrents)))

        return "\n".join(lines)


class ScanFormatter:
    """Format malware scan results for terminal display."""

    def format(self, result: dict) -> str:
        if result.get("status") == "error":
            return "❌ " + result["message"]

        lines = []
        s = result["summary"]
        lines.append("🛡️ Malware Scan — " + result["windows_path"] + "\n")

        if s["safe"]:
            lines.append("  ✅ SAFE — No critical or high-severity issues detected")
        else:
            lines.append(
                "  ⚠️ ISSUES FOUND — " +
                str(s["critical"]) + " critical, " +
                str(s["high"]) + " high, " +
                str(s["medium"]) + " medium, " +
                str(s["low"]) + " low"
            )

        dr = result.get("defender_scan", {})
        if dr:
            if dr.get("threats_found"):
                lines.append("\n  🚨 Windows Defender threats detected:\n    " + dr["threats_found"][:200])
            elif dr.get("status") == "timeout":
                lines.append("\n  ⏳ Defender scan: timed out")
            elif dr.get("status") == "error":
                lines.append("\n  ❌ Defender scan failed: " + dr.get("message", "unknown"))
            else:
                lines.append("\n  ✅ Windows Defender: no threats detected")

        for f in result.get("suspicious_files", []):
            icon = "🔴" if f["severity"] == "HIGH" else "🟡" if f["severity"] == "MEDIUM" else "🟢"
            lines.append("  " + icon + " [" + f["severity"] + "] " + f["reason"])

        return "\n".join(lines)


class GapFormatter:
    """Format gap analysis results for terminal display."""

    def format(self, gap_dict: dict) -> str:
        media_type = gap_dict.get("media_type", "unknown")
        query = gap_dict.get("query", "?")
        source = gap_dict.get("source", "?")
        total = gap_dict.get("total_expected", 0)
        existing_count = gap_dict.get("existing_count", 0)
        missing_count = gap_dict.get("missing_count", 0)
        completion = gap_dict.get("completion_pct", 0)
        is_complete = gap_dict.get("is_complete", False)
        metadata = gap_dict.get("metadata", {})

        if media_type == "show":
            return self._format_show(query, source, total, existing_count,
                                     missing_count, completion, is_complete, metadata, gap_dict)
        elif media_type == "music":
            return self._format_music(query, source, total, existing_count,
                                      missing_count, completion, is_complete, metadata, gap_dict)
        elif media_type == "movie":
            return self._format_movie(query, source, total, existing_count,
                                      missing_count, completion, is_complete, metadata, gap_dict)
        else:
            return "Unknown media type: " + media_type

    def _format_show(self, query, source, total, existing, missing,
                     completion, is_complete, metadata, gap_dict) -> str:
        show_name = metadata.get("show_name", query)
        status = metadata.get("status", "?")
        seasons = metadata.get("seasons", {})

        lines = []
        lines.append("📺 " + show_name + " — Gap Analysis [" + source + "]")
        lines.append("Status: " + status + " | Episodes: " + str(existing) + "/" + str(total) + " (" + str(completion) + "%)\n")

        if is_complete:
            lines.append("✅ You have all episodes!")
            return "\n".join(lines)

        # Season summary
        if seasons:
            lines.append("===== SEASON SUMMARY =====")
            for season_name, info in seasons.items():
                total_s = info["total"]
                existing_s = info["existing"]
                missing_s = info["missing"]
                comp = info["completion"]
                bar_len = 20
                filled = int(existing_s / max(total_s, 1) * bar_len)
                bar = "█" * filled + "░" * (bar_len - filled)
                lines.append(
                    "  " + season_name + ": " + bar + " " + comp +
                    " (" + str(existing_s) + "/" + str(total_s) +
                    ", " + str(missing_s) + " missing)"
                )
            lines.append("")

        # Missing episodes
        missing_list = gap_dict.get("missing", [])
        if missing_list:
            lines.append("===== MISSING EPISODES =====")
            by_season = {}
            for ep in missing_list:
                s = ep.get("season", 0)
                by_season.setdefault(s, []).append(ep)

            for s in sorted(by_season.keys()):
                lines.append("\n  Season " + str(s) + ":")
                for ep in sorted(by_season[s], key=lambda x: x.get("episode", 0)):
                    unaired = " (UNAIRED)" if ep.get("unaired") else ""
                    airdate = ep.get("airdate", "")
                    date_str = " — " + airdate if airdate else ""
                    lines.append(
                        "    ❌ " + ep["code"] + " " + ep.get("name", "?") +
                        date_str + unaired
                    )

        # Existing episodes (compact)
        existing_list = gap_dict.get("existing", [])
        if existing_list:
            lines.append("\n===== EXISTING EPISODES =====")
            existing_codes = [ep["code"] for ep in sorted(existing_list, key=lambda x: (x.get("season", 0), x.get("episode", 0)))]
            # Show in rows of 10
            for i in range(0, len(existing_codes), 10):
                chunk = existing_codes[i:i+10]
                lines.append("  ✅ " + "  ".join(chunk))

        return "\n".join(lines)

    def _format_music(self, query, source, total, existing, missing,
                      completion, is_complete, metadata, gap_dict) -> str:
        artist = metadata.get("artist_name", query)

        lines = []
        lines.append("🎵 " + artist + " — Discography Gap Analysis [" + source + "]")
        lines.append("Albums: " + str(existing) + "/" + str(total) + " (" + str(completion) + "%)\n")

        if is_complete:
            lines.append("✅ You have all albums!")
            return "\n".join(lines)

        # Missing albums
        missing_list = gap_dict.get("missing", [])
        if missing_list:
            lines.append("===== MISSING ALBUMS =====")
            for album in sorted(missing_list, key=lambda x: x.get("year", "")):
                year = album.get("year", "????")
                atype = album.get("type", "Album")
                secondary = ", ".join(album.get("secondary_types", []))
                type_str = atype
                if secondary:
                    type_str += " (" + secondary + ")"
                lines.append("  ❌ [" + year + "] " + album["title"] + " — " + type_str)

        # Existing albums
        existing_list = gap_dict.get("existing", [])
        if existing_list:
            lines.append("\n===== EXISTING ALBUMS =====")
            for album in sorted(existing_list, key=lambda x: x.get("year", "")):
                year = album.get("year", "????")
                lines.append("  ✅ [" + year + "] " + album["title"])

        return "\n".join(lines)

    def _format_movie(self, query, source, total, existing, missing,
                      completion, is_complete, metadata, gap_dict) -> str:
        title = metadata.get("movie_title", query)
        year = metadata.get("movie_year", "")

        lines = []
        header = "🎬 " + title
        if year:
            header += " (" + str(year) + ")"
        header += " — Franchise/Sequel Gap Analysis [" + source + "]"
        lines.append(header)
        lines.append("Entries: " + str(existing) + "/" + str(total) + " (" + str(completion) + "%)\n")

        if is_complete:
            lines.append("✅ You have all entries in the franchise!")
            return "\n".join(lines)

        # Missing entries
        missing_list = gap_dict.get("missing", [])
        if missing_list:
            lines.append("===== MISSING ENTRIES =====")
            for entry in missing_list:
                kind = entry.get("kind", "related")
                year_str = " (" + str(entry["year"]) + ")" if entry.get("year") else ""
                lines.append("  ❌ " + entry["title"] + year_str + " — " + kind)

        # Existing entries
        existing_list = gap_dict.get("existing", [])
        if existing_list:
            lines.append("\n===== EXISTING ENTRIES =====")
            for entry in existing_list:
                kind = entry.get("kind", "original")
                year_str = " (" + str(entry["year"]) + ")" if entry.get("year") else ""
                lines.append("  ✅ " + entry["title"] + year_str + " — " + kind)

        return "\n".join(lines)
