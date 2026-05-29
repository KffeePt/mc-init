# qbittorrent-plex-refresh.ps1
# Deploy to: D:\Scripts\qbittorrent-plex-refresh.ps1
# Configure in qBittorrent GUI: Tools -> Options -> Downloads -> "Run external program on torrent completion"
# Command to paste:
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Scripts\qbittorrent-plex-refresh.ps1" "%F" "%N" "%L" "%D"
#
# qBittorrent placeholders:
#   %F = content path (folder or single file)
#   %N = torrent name
#   %L = category
#   %D = save path

param(
    [string]$ContentPath,
    [string]$TorrentName,
    [string]$Category,
    [string]$SavePath
)

$logFile = "D:\Scripts\qbittorrent-plex-refresh.log"
$plexToken = "<PLEX_TOKEN_HERE>"
$plexBase = "http://localhost:32400"

function Log($msg) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp | $msg" | Out-File -Append -FilePath $logFile -Encoding utf8
}

Log "=== Torrent completed ==="
Log "  ContentPath: $ContentPath"
Log "  TorrentName: $TorrentName"
Log "  SavePath: $SavePath"

# Only act on D:\Shows\ downloads
if ($SavePath -notmatch '^D:\\Shows') {
    Log "  SKIP: SavePath is not under D:\Shows"
    exit 0
}

# Small delay to let Windows finish file handles
Start-Sleep -Seconds 3

# Refresh Plex More Shows section (section 6)
try {
    Log "  Triggering Plex refresh for section 6 (More Shows)..."
    $r = Invoke-WebRequest -UseBasicParsing `
        -Uri "$plexBase/library/sections/6/refresh" `
        -Method Get `
        -TimeoutSec 30 `
        -Headers @{"X-Plex-Token" = $plexToken}
    Log "  Plex refresh OK: HTTP $($r.StatusCode)"
} catch {
    Log "  Plex refresh FAILED: $($_.Exception.Message)"
    exit 1
}

Log "=== Done ==="
