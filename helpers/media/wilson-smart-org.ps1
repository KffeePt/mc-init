# wilson-smart-org.ps1
# Purpose: manual Wilson media organization runner for completed qBittorrent items and review queue decisions.
# Date: 2026-05-28
# Side effects: may remove completed torrents from qBittorrent while keeping files, flatten completed show roots, write D:\Review and Desktop review.yaml, refresh Plex, and optionally apply review TUI decisions.
# Safety: skips incomplete active content paths; conflict default is remote/new kept in library while old/local is queued under D:\Review.

param(
    [switch]$NoTui,
    [switch]$ReviewOnly,
    [switch]$AllShows,
    [switch]$HashOnly
)

$ErrorActionPreference = "Continue"
$lib = "C:\Users\santi\Documents\Hermes\Scripts\qbittorrent-batch-lib.ps1"
. $lib

function Write-WilsonLine([string]$Message, [string]$Color = "Gray") {
    Write-Host $Message -ForegroundColor $Color
    Log-HermesQb "SMART_ORG: $Message" $script:HermesQbFinishedLog
}

function Get-WilsonScalar($Value) {
    if ($Value -is [array]) {
        if ($Value.Count -eq 0) { return $null }
        return $Value[0]
    }
    return $Value
}

function Get-WilsonCompletedShowRoots {
    $roots = [ordered]@{}
    $hashes = @()
    $torrents = @(Get-HermesQbTorrents $script:HermesQbFinishedLog)
    foreach ($t in $torrents) {
        $mediaType = Get-HermesMediaType ([string](Get-WilsonScalar $t.category)) ([string](Get-WilsonScalar $t.save_path)) ([string](Get-WilsonScalar $t.content_path))
        if ($mediaType -ne "show") { continue }
        $progress = 0.0
        $progressValue = Get-WilsonScalar $t.progress
        if ($null -ne $progressValue) { $progress = [double]$progressValue }
        if ($progress -ge 0.999) {
            $item = New-HermesRegistryItem ([string](Get-WilsonScalar $t.name)) ([string](Get-WilsonScalar $t.content_path)) ([string](Get-WilsonScalar $t.save_path)) ([string](Get-WilsonScalar $t.hash)) ([string](Get-WilsonScalar $t.category)) "finished"
            $root = Resolve-HermesShowRoot $item
            if ($root -and (Test-Path -LiteralPath $root -PathType Container)) { $roots[$root] = $true }
            $hashValue = Get-WilsonScalar $t.hash
            if ($hashValue) { $hashes += [string]$hashValue }
        }
    }

    $reg = Read-HermesRegistry $script:HermesQbFinishedLog
    foreach ($p in $reg.items.GetEnumerator()) {
        $item = $p.Value
        if ($item.media_type -eq "show" -and $item.status -in @("finished","flattened")) {
            $root = Resolve-HermesShowRoot $item
            if ($root -and (Test-Path -LiteralPath $root -PathType Container)) { $roots[$root] = $true }
            if ($item.info_hash) { $hashes += [string]$item.info_hash }
        }
    }

    return [pscustomobject]@{ roots = @($roots.Keys); hashes = @($hashes | Select-Object -Unique) }
}

function Get-WilsonIncompleteShowRoots {
    $blocked = @{}
    $torrents = @(Get-HermesQbTorrents $script:HermesQbFinishedLog)
    foreach ($t in $torrents) {
        $mediaType = Get-HermesMediaType ([string](Get-WilsonScalar $t.category)) ([string](Get-WilsonScalar $t.save_path)) ([string](Get-WilsonScalar $t.content_path))
        if ($mediaType -ne "show") { continue }
        $progress = 0.0
        $progressValue = Get-WilsonScalar $t.progress
        if ($null -ne $progressValue) { $progress = [double]$progressValue }
        if ($progress -lt 0.999) {
            $item = New-HermesRegistryItem ([string](Get-WilsonScalar $t.name)) ([string](Get-WilsonScalar $t.content_path)) ([string](Get-WilsonScalar $t.save_path)) ([string](Get-WilsonScalar $t.hash)) ([string](Get-WilsonScalar $t.category)) "active"
            $root = Resolve-HermesShowRoot $item
            if ($root) { $blocked[$root] = $true }
        }
    }
    return $blocked
}

function Get-WilsonCompletedMovieRoots {
    $roots = [ordered]@{}
    $hashes = @()
    $torrents = @(Get-HermesQbTorrents $script:HermesQbFinishedLog)
    foreach ($t in $torrents) {
        $mediaType = Get-HermesMediaType ([string](Get-WilsonScalar $t.category)) ([string](Get-WilsonScalar $t.save_path)) ([string](Get-WilsonScalar $t.content_path))
        if ($mediaType -ne "movie") { continue }
        $progress = 0.0
        $progressValue = Get-WilsonScalar $t.progress
        if ($null -ne $progressValue) { $progress = [double]$progressValue }
        if ($progress -ge 0.999) {
            $item = New-HermesRegistryItem ([string](Get-WilsonScalar $t.name)) ([string](Get-WilsonScalar $t.content_path)) ([string](Get-WilsonScalar $t.save_path)) ([string](Get-WilsonScalar $t.hash)) ([string](Get-WilsonScalar $t.category)) "finished"
            $root = Resolve-HermesMovieRoot $item
            if ($root -and (Test-Path -LiteralPath $root -PathType Container)) { $roots[$root] = $true }
            $hashValue = Get-WilsonScalar $t.hash
            if ($hashValue) { $hashes += [string]$hashValue }
        }
    }
    return [pscustomobject]@{ roots = @($roots.Keys); hashes = @($hashes | Select-Object -Unique) }
}

New-Item -ItemType Directory -Force -Path $script:HermesReviewCurrent | Out-Null
if (-not (Test-Path -LiteralPath $script:HermesReviewIndex)) { Write-HermesReviewIndex @() "initialized" }
else { Write-HermesReviewIndex @(Get-HermesReviewItems) "refreshed" }

Write-WilsonLine "Wilson smart_org started." "Cyan"
if ($HashOnly) { Write-WilsonLine "HashOnly requested, but this runner now performs smart organization too." "Yellow" }

$totalMoved = 0
$totalFailed = 0
$totalCollisions = 0
$movieMoved = 0
$movieFailed = 0
$movieCollisions = 0
$roots = @()
$movieRoots = @()
$hashes = @()

if (-not $ReviewOnly) {
    $completed = Get-WilsonCompletedShowRoots
    $roots += @($completed.roots)
    $hashes += @($completed.hashes)
    $completedMovies = Get-WilsonCompletedMovieRoots
    $movieRoots += @($completedMovies.roots)
    $hashes += @($completedMovies.hashes)

    if ($AllShows) {
        $blocked = Get-WilsonIncompleteShowRoots
        Get-ChildItem -LiteralPath "D:\Shows" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
            if (-not $blocked.ContainsKey($_.FullName)) { $roots += $_.FullName }
        }
    }

    $roots = @($roots | Where-Object { $_ } | Select-Object -Unique)
    $movieRoots = @($movieRoots | Where-Object { $_ } | Select-Object -Unique)
    $hashes = @($hashes | Where-Object { $_ } | Select-Object -Unique)

    if ($hashes.Count -gt 0) {
        Remove-HermesQbTorrentsKeepFiles $hashes $script:HermesQbFinishedLog | Out-Null
        Start-Sleep -Seconds 2
    }

    foreach ($root in $roots) {
        Write-WilsonLine "Flattening show: $root" "Gray"
        $result = Flatten-HermesShowRoot $root $script:HermesQbFinishedLog
        $totalMoved += [int]$result.copied
        $totalFailed += [int]$result.failed
        $totalCollisions += [int]$result.collisions
    }
    foreach ($root in $movieRoots) {
        Write-WilsonLine "Flattening movie: $root" "Gray"
        $result = Flatten-HermesMovieRoot $root $script:HermesQbFinishedLog
        $movieMoved += [int]$result.moved
        $movieFailed += [int]$result.failed
        $movieCollisions += [int]$result.collisions
    }

    if ($roots.Count -gt 0 -and ($totalMoved -gt 0 -or $totalCollisions -gt 0)) {
        Invoke-HermesPlexShowsRefresh $script:HermesQbFinishedLog | Out-Null
    }
    if ($movieRoots.Count -gt 0 -and ($movieMoved -gt 0 -or $movieCollisions -gt 0)) {
        Invoke-HermesPlexMoviesRefresh $script:HermesQbFinishedLog | Out-Null
    }
}

Write-HermesReviewIndex @(Get-HermesReviewItems) "smart_org_completed"
Write-WilsonLine "Flatten show_roots=$($roots.Count) show_moved=$totalMoved show_failed=$totalFailed movie_roots=$($movieRoots.Count) movie_moved=$movieMoved movie_failed=$movieFailed review_items=$((@(Get-HermesReviewItems | Where-Object { $_.status -eq 'open' })).Count)" "Green"
Write-Host ""
Write-Host "Review YAML:" -ForegroundColor Cyan
Write-Host "  D:\Review\current\review.yaml"
Write-Host ""

if (-not $NoTui) {
    Invoke-HermesReviewTui $script:HermesQbFinishedLog
}

Write-HermesReviewIndex @(Get-HermesReviewItems) "smart_org_exit"
Write-WilsonLine "Wilson smart_org finished." "Cyan"
