"""qBittorrent client — PowerShell bridge for WSL-to-Windows API calls.

From WSL, curl/curl.exe CANNOT authenticate to qBittorrent due to CSRF
protection rejecting cross-origin requests. The ONLY working approach
is PowerShell running natively on Windows, which is treated as same-origin.
"""

import json
import os
import subprocess
from typing import Optional, Dict, Any, List


class QBittorrentClient:
    """qBittorrent Web API client via PowerShell bridge."""

    def __init__(self, host: str = "localhost", port: int = 8080,
                 username: str | None = None, password: str | None = None):
        self.host = host
        self.port = port
        self.username = username or os.getenv("QBITTORRENT_USERNAME") or os.getenv("QBT_USERNAME") or ""
        self.password = password or os.getenv("QBITTORRENT_PASSWORD") or os.getenv("QBT_PASSWORD") or ""
        # qBittorrent can be configured to bypass Web UI auth for localhost.
        # On Xan's Windows host this is the active setup; the PowerShell bridge
        # runs natively on Windows localhost, so unauthenticated local API calls
        # are valid. If credentials are present, use them. Otherwise try the
        # local bypass instead of failing before the request is attempted.

    @property
    def base_url(self) -> str:
        return "http://" + self.host + ":" + str(self.port) + "/api/v2"

    def _login_url(self) -> str:
        return self.base_url + "/auth/login"

    def _api_url(self, endpoint: str) -> str:
        return self.base_url + "/" + endpoint

    def _login_body(self) -> str:
        return "username=" + self.username + "&password=" + self.password

    def _ps_request(self, endpoint: str, body_var: Optional[str] = None,
                    method: str = "POST") -> Optional[str]:
        """Execute a qBittorrent API request via PowerShell bridge.

        Args:
            endpoint: API endpoint (e.g. 'torrents/info')
            body_var: PowerShell variable assignment for POST body (e.g. "$body = @{...}")
            method: HTTP method

        Returns:
            Response content string, or None on failure.
        """
        login_url = self._login_url()
        api_url = self._api_url(endpoint)
        login_body = self._login_body()

        login_body_ps = "$loginBody = @{username='" + self.username + "'; password='" + self.password + "'}\n"

        if body_var:
            if self.username and self.password:
                ps_cmd = (
                    "$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession\n"
                    + login_body_ps +
                    "$r = Invoke-WebRequest -Uri '" + login_url + "' `\n"
                    "    -Method POST -Body $loginBody -WebSession $session -UseBasicParsing -ErrorAction Stop\n"
                    + body_var + "\n"
                    "$r2 = Invoke-WebRequest -Uri '" + api_url + "' `\n"
                    "    -Method POST -Body $body -WebSession $session -UseBasicParsing -ErrorAction Stop\n"
                    "[Console]::Out.Write($r2.Content)\n"
                )
            else:
                ps_cmd = (
                    body_var + "\n"
                    "$r2 = Invoke-WebRequest -Uri '" + api_url + "' `\n"
                    "    -Method POST -Body $body -UseBasicParsing -ErrorAction Stop\n"
                    "[Console]::Out.Write($r2.Content)\n"
                )
        else:
            if self.username and self.password:
                ps_cmd = (
                    "$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession\n"
                    + login_body_ps +
                    "$r = Invoke-WebRequest -Uri '" + login_url + "' `\n"
                    "    -Method POST -Body $loginBody -WebSession $session -UseBasicParsing -ErrorAction Stop\n"
                    "$r2 = Invoke-WebRequest -Uri '" + api_url + "' `\n"
                    "    -WebSession $session -UseBasicParsing -ErrorAction Stop\n"
                    "[Console]::Out.Write($r2.Content)\n"
                )
            else:
                ps_cmd = (
                    "$r2 = Invoke-WebRequest -Uri '" + api_url + "' `\n"
                    "    -UseBasicParsing -ErrorAction Stop\n"
                    "[Console]::Out.Write($r2.Content)\n"
                )

        try:
            result = subprocess.run(
                ["powershell.exe", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except (subprocess.TimeoutExpired, Exception):
            return None

    def add_torrent(self, magnet_link: str, save_path: str, media_type: Optional[str] = None) -> Dict[str, Any]:
        """Add a torrent to qBittorrent.

        Args:
            magnet_link: Magnet URI
            save_path: Windows save path (e.g. 'D:\\Movies\\')
            media_type: Optional explicit media type: movie, show/tv, or music.
                When supplied, this is written as the qBittorrent category so
                post-download hooks do not infer from fragile torrent names.

        Returns:
            {"status": "ok"|"error", "message": str, "data": optional}
        """
        # Escape backslashes for PowerShell string literal
        escaped_path = save_path.replace("\\", "\\\\")
        category = None
        if media_type:
            mt = media_type.strip().lower()
            if mt in {"show", "tv", "series"}:
                category = "tv"
            elif mt in {"movie", "movies"}:
                category = "movie"
            elif mt == "music":
                category = "music"

        body_items = "urls='" + magnet_link + "'; savepath='" + escaped_path + "'"
        if category:
            body_items += "; category='" + category + "'"
        body_var = "$body = @{" + body_items + "}"

        result = self._ps_request("torrents/add", body_var=body_var)

        if result is not None:
            try:
                data = json.loads(result)
                if data.get("success_count", 0) > 0:
                    return {"status": "ok", "message": "Added successfully", "data": data}
                return {"status": "error", "message": result}
            except json.JSONDecodeError:
                # Empty response often means success (HTTP 204)
                if not result:
                    return {"status": "ok", "message": "Added successfully (HTTP 204)"}
                return {"status": "error", "message": "Invalid response: " + result[:200]}

        return {"status": "error", "message": "Failed to connect to qBittorrent"}

    def get_torrents(self, filter_name: Optional[str] = None) -> Dict[str, Any]:
        """Get list of torrents from qBittorrent.

        Args:
            filter_name: Optional name substring to filter by

        Returns:
            {"status": "ok"|"error", "torrents": list}
        """
        result = self._ps_request("torrents/info")

        if result is None:
            # Check if qBittorrent is even running
            if not self._is_running():
                return {"status": "error", "message": "qBittorrent is not running"}
            return {"status": "error", "message": "qBittorrent Web UI not accessible (port " + str(self.port) + ")."}

        try:
            torrents = json.loads(result)
        except json.JSONDecodeError as e:
            return {"status": "error", "message": "Failed to parse torrent list: " + str(e)}

        if not isinstance(torrents, list):
            return {"status": "error", "message": "Unexpected response format"}

        parsed = []
        for t in torrents:
            name = t.get("name", "Unknown")
            if filter_name and filter_name.lower() not in name.lower():
                continue
            parsed.append(self._parse_torrent(t))

        return {"status": "ok", "torrents": parsed}

    @staticmethod
    def _parse_torrent(t: dict) -> Dict[str, Any]:
        """Parse a raw qBittorrent torrent dict into a display-friendly format."""
        name = t.get("name", "Unknown")
        size_bytes = t.get("size", 0)
        progress_pct = t.get("progress", 0) * 100
        download_speed = t.get("dlspeed", 0)
        seeds = t.get("num_seeds", 0)
        eta = t.get("eta", -1)

        if progress_pct >= 100:
            status = "✅ Complete"
        elif download_speed > 0:
            status = "⬇️ Downloading"
        elif seeds == 0:
            status = "⏳ Waiting for peers"
        else:
            status = "⏸️ Paused/Queued"

        return {
            "name": name,
            "status": status,
            "progress": f"{progress_pct:.1f}%",
            "progress_pct": progress_pct,
            "size": _human_size(t.get("size", 0)),
            "size_bytes": t.get("size", 0),
            "download_speed": _human_speed(download_speed),
            "upload_speed": _human_speed(t.get("upspeed", 0)),
            "eta": _human_eta(eta),
            "seeds": seeds,
            "peers": t.get("num_leechs", 0),
            "info_hash": t.get("hash", ""),
            "category": t.get("category", ""),
            "save_path": t.get("save_path", ""),
            "content_path": t.get("content_path", ""),
        }

    @staticmethod
    def _is_running() -> bool:
        """Check if qBittorrent process is running on Windows."""
        try:
            result = subprocess.run(
                ["tasklist.exe"], capture_output=True, text=True, timeout=5,
            )
            return "qbittorrent" in result.stdout.lower()
        except Exception:
            return False


# ─── Human-readable formatters ──────────────────────────────────────

def _human_size(b: int) -> str:
    if b >= 1024**3:
        return f"{b / (1024**3):.2f} GiB"
    if b >= 1024**2:
        return f"{b / (1024**2):.1f} MiB"
    return f"{b / 1024:.0f} KiB"


def _human_speed(bps: int) -> str:
    if bps >= 1024**2:
        return f"{bps / (1024**2):.1f} MB/s"
    if bps >= 1024:
        return f"{bps / 1024:.0f} KB/s"
    return f"{bps} B/s"


def _human_eta(secs: int) -> str:
    if secs < 0:
        return "∞"
    hrs = secs // 3600
    mins = (secs % 3600) // 60
    s = secs % 60
    if hrs > 0:
        return f"{hrs}h {mins}m"
    if mins > 0:
        return f"{mins}m {s}s"
    return f"{s}s"
