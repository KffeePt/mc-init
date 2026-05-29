# qbittorrent-flatten-refresh.ps1 — TEMPLATE
# Deploy to: D:\Scripts\qbittorrent-flatten-refresh.ps1
# Then configure in qBittorrent: Tools → Options → Downloads → Run external program on torrent completion:
#   powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\Scripts\qbittorrent-flatten-refresh.ps1" "%F" "%N" "%L" "%D"
#
# WHAT IT DOES:
#   1. Scans the save path for media files with S##E## patterns in nested pack folders
#   2. Copies them into flat S1/, S2/, S3/ season folders (matching sidecar .srt/.sub/.nfo files too)
#   3. Removes empty leftover nested pack folders
#   4. Triggers Plex "More Shows" (section 6) refresh via API
#
# IDEMPOTENT — safe to run on already-flattened folders.
# HANDLES LOCKED FILES — uses Copy-Item + conditional-delete (qBittorrent seed handles block Move-Item).
#
# Replace <PLEX_TOKEN> with the actual token (retrieve from HKCU:\Software\Plex, Inc.\Plex Media Server)

param(
    [string]$ContentPath,
    [string]$TorrentName,
    [string]$Category,
    [string]$SavePath
)

$ErrorActionPreference = "Continue"
$logFile = "D:\Scripts\qbittorrent-flatten-refresh.log"
$plexToken = "<PLEX_TOKEN>"
$plexBase = "http://localhost:32400"

function Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $logFile -Value "$ts | $msg" -Encoding UTF8
}

Log "=== Torrent completed ==="
Log "  TorrentName: $TorrentName"
Log "  SavePath:    $SavePath"

# Only act on D:\Shows\ downloads (not Movies, Music, etc.)
if ($SavePath -notmatch '^D:\\Shows') {
    Log "  SKIP: not under D:\Shows"
    exit 0
}

Start-Sleep -Seconds 3

$showRoot = $SavePath.TrimEnd("\")
if (-not (Test-Path $showRoot)) {
    Log "  SKIP: $showRoot missing"
    exit 0
}

Log "  Show root: $showRoot"

$epRegex = "[Ss](\d{1,2})[Ee]\d{1,2}"
$sidecarExts = @(".srt", ".sub", ".idx", ".ass", ".ssa", ".vtt", ".nfo")
$copied = 0; $deleted = 0; $failed = 0; $dirsRemoved = 0
$seasonDirs = @{}
$epBaseNames = @{}

$allFiles = Get-ChildItem -Path $showRoot -File -Recurse -Depth 6 -ErrorAction SilentlyContinue

# Build episode base-name -> season number map (for sidecar matching)
foreach ($f in $allFiles) {
    if ($f.Name -match $epRegex) {
        $epBaseNames[$f.BaseName] = [int]$Matches[1]
    }
}

# Process files: copy to flat season folder, try to delete source
foreach ($f in $allFiles) {
    $sn = $null
    if ($f.Name -match $epRegex) {
        $sn = [int]$Matches[1]
    } else {
        $x = $f.Extension.ToLower()
        if ($x -in $sidecarExts) {
            foreach ($b in $epBaseNames.Keys) {
                if ($f.BaseName.StartsWith($b)) { $sn = $epBaseNames[$b]; break }
            }
        }
    }
    if ($null -eq $sn) { continue }

$season = "S$sn"
    $td = Join-Path $showRoot $season
    if ($f.DirectoryName.TrimEnd("\") -eq $td.TrimEnd("\")) { continue }

    if (-not $seasonDirs.ContainsKey($season)) {
        New-Item -ItemType Directory -Force -Path $td | Out-Null
        $seasonDirs[$season] = $true
    }

    $cleanName = $f.Name
    # Remove URLs like www.UIndex.org
    $cleanName = $cleanName -replace '(?i)www\.[a-z0-9\-]+\.[a-z]{2,}(?:\s*-\s*)?', ''
    # Remove bracketed text often used for release groups like [EZTVx.to]
    $cleanName = $cleanName -replace '\[.*?\]', ''
    # Remove multiple spaces
    $cleanName = $cleanName -replace '\s+', ' '
    $cleanName = $cleanName.Trim()

    $dest = Join-Path $td $cleanName

    if (Test-Path -LiteralPath $dest) {
        try {
            if ((Get-Item -LiteralPath $dest).Length -eq (Get-Item -LiteralPath $f.FullName).Length) {
                Remove-Item -LiteralPath $f.FullName -Force -ErrorAction Stop
                $deleted++
                continue
            }
        } catch {}
    }

    try {
        # Copy first (works on seed-locked files), then try to delete original
        Copy-Item -LiteralPath $f.FullName -Destination $dest -Force -ErrorAction Stop
        $copied++
        try { Remove-Item -LiteralPath $f.FullName -Force -ErrorAction Stop; $deleted++ } catch {}
    } catch {
        Log "  COPY FAILED: $($f.Name)"
        $failed++
    }
}

Log "  copied=$copied deleted=$deleted failed=$failed"

# Remove empty nested dirs (keep only show root + S# season folders)
$keep = @{ $showRoot = $true }
foreach ($s in $seasonDirs.Keys) { $keep[(Join-Path $showRoot $s)] = $true }

Get-ChildItem -Path $showRoot -Directory -Recurse -Depth 6 -ErrorAction SilentlyContinue |
    Sort-Object { $_.FullName.Length } -Descending |
    ForEach-Object {
        if (-not $keep.ContainsKey($_.FullName)) {
            if ((Get-ChildItem -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue).Count -eq 0) {
                Remove-Item -LiteralPath $_.FullName -Force -Recurse -ErrorAction SilentlyContinue
                $dirsRemoved++
            }
        }
    }

Log "  empty dirs removed=$dirsRemoved"

# Plex refresh — section 6 = "More Shows" → D:\Shows
try {
    Log "  Plex refresh section 6..."
    $r = Invoke-WebRequest -UseBasicParsing -Uri "$plexBase/library/sections/6/refresh" -Method Get -TimeoutSec 30 -Headers @{"X-Plex-Token"=$plexToken}
    Log "  Plex: HTTP $($r.StatusCode)"
} catch {
    Log "  Plex FAILED: $($_.Exception.Message)"
}

Log "=== Done ==="
