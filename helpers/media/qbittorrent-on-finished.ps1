# qbittorrent-on-finished.ps1
# qBittorrent: Run external program on torrent finished
# Smart batching: refresh telemetry, then either wait for near-finished items or flush completed subset.

param(
    [string]$ContentPath,
    [string]$TorrentName,
    [string]$Category,
    [string]$SavePath,
    [string]$InfoHash
)

$ErrorActionPreference = "Continue"
$lib = "C:\Users\santi\Documents\Hermes\Scripts\qbittorrent-batch-lib.ps1"
. $lib

New-Item -ItemType Directory -Force -Path $script:HermesQbScriptDir | Out-Null
Log-HermesQb "=== FINISHED: $TorrentName ===" $script:HermesQbFinishedLog
Log-HermesQb "  SavePath: $SavePath" $script:HermesQbFinishedLog
Log-HermesQb "  ContentPath: $ContentPath" $script:HermesQbFinishedLog
Log-HermesQb "  InfoHash: $InfoHash" $script:HermesQbFinishedLog

$mediaType = Get-HermesMediaType $Category $SavePath $ContentPath
if ($mediaType -eq "movie") {
    Log-HermesQb "  MOVIE_FINISHED: smart movie flatten path" $script:HermesQbFinishedLog
    $movieItem = New-HermesRegistryItem $TorrentName $ContentPath $SavePath $InfoHash $Category "finished"
    $movieRoot = Resolve-HermesMovieRoot $movieItem
    if ($InfoHash) { Remove-HermesQbTorrentsKeepFiles @($InfoHash) $script:HermesQbFinishedLog | Out-Null; Start-Sleep -Seconds 2 }
    if ($movieRoot) {
        $movieResult = Flatten-HermesMovieRoot $movieRoot $script:HermesQbFinishedLog
        if ([int]$movieResult.moved -gt 0 -or [int]$movieResult.collisions -gt 0) { Invoke-HermesPlexMoviesRefresh $script:HermesQbFinishedLog | Out-Null }
        Log-HermesQb "=== Movie Done root=$movieRoot moved=$($movieResult.moved) failed=$($movieResult.failed) collisions_for_review=$($movieResult.collisions) ===" $script:HermesQbFinishedLog
    } else {
        Log-HermesQb "  MOVIE SKIP: unresolved movie root | save=$SavePath | content=$ContentPath" $script:HermesQbFinishedLog
    }
    exit 0
}
if ($mediaType -ne "show") {
    Log-HermesQb "  IGNORE_NON_MEDIA: media_type=$mediaType category=$Category; flattener not applicable" $script:HermesQbFinishedLog
    exit 0
}

$key = Get-HermesRegistryKey $TorrentName $SavePath $InfoHash
$mutex = New-Object System.Threading.Mutex($false, $script:HermesQbMutexName)
$hasLock = $false
$rootsToFlatten = [ordered]@{}
$decision = $null
$reg = $null

try {
    $hasLock = $mutex.WaitOne([TimeSpan]::FromSeconds(30))
    if (-not $hasLock) { throw "Timed out waiting for registry lock" }

    $reg = Read-HermesRegistry $script:HermesQbFinishedLog
    if (-not $reg.items.Contains($key)) {
        Log-HermesQb "  Registry missing finished item; adding completed key=$key" $script:HermesQbFinishedLog
        $reg.items[$key] = New-HermesRegistryItem $TorrentName $ContentPath $SavePath $InfoHash $Category "finished"
        $reg.items[$key].finished_at = (Get-Date -Format "o")
    } else {
        $reg.items[$key].status = "finished"
        $reg.items[$key].finished_at = (Get-Date -Format "o")
        $reg.items[$key].name = $TorrentName
        $reg.items[$key].content_path = $ContentPath
        $reg.items[$key].save_path = $SavePath
        $reg.items[$key].info_hash = $InfoHash
        $reg.items[$key].category = $Category
        $reg.items[$key].media_type = $mediaType
        $reg.items[$key].show_root = Resolve-HermesShowRoot $reg.items[$key]
    }

    $torrents = Get-HermesQbTorrents $script:HermesQbFinishedLog
    $reg = Update-HermesRegistryTelemetry $reg $torrents $script:HermesQbFinishedLog
    $decision = Get-HermesFlushDecision $reg
    $reg.decision = $decision

    if (-not $decision.should_flush) {
        Write-HermesRegistry $reg
        Log-HermesQb "  WAIT: $($decision.reason) | finished=$($decision.finished_count) active=$($decision.active_count)" $script:HermesQbFinishedLog
        foreach ($a in $decision.active) {
            Log-HermesQb "    ACTIVE_BLOCKER: $($a.name) | group=$($a.group) eta=$($a.eta) reliability=$($a.reliability) progress=$($a.progress)" $script:HermesQbFinishedLog
        }
        exit 0
    }

    Log-HermesQb "  FLUSH: $($decision.reason) | finished=$($decision.finished_count) active=$($decision.active_count)" $script:HermesQbFinishedLog
    foreach ($p in $reg.items.GetEnumerator()) {
        $item = $p.Value
        if ($item.media_type -eq "show" -and $item.status -eq "finished") {
            $root = Resolve-HermesShowRoot $item
            if ($null -eq $root) {
                Log-HermesQb "  SKIP: unresolved show root | $($item.name) | save=$($item.save_path) | content=$($item.content_path)" $script:HermesQbFinishedLog
                $item.status = "error"
                continue
            }
            $rootsToFlatten[$root] = $true
            $item.status = "flattened"
        }
    }

    Write-HermesRegistry $reg
} catch {
    Log-HermesQb "  REGISTRY_FAILED: $($_.Exception.Message); processing current item only" $script:HermesQbFinishedLog
    $current = New-HermesRegistryItem $TorrentName $ContentPath $SavePath $InfoHash $Category "finished"
    $root = Resolve-HermesShowRoot $current
    if ($root) { $rootsToFlatten[$root] = $true }
} finally {
    if ($hasLock) { $mutex.ReleaseMutex() | Out-Null }
    $mutex.Dispose()
}

Start-Sleep -Seconds 3
$totalFailed = 0
$totalCollisions = 0
$totalMoved = 0
$hashesToDetach = @()
if ($reg) {
    foreach ($p in $reg.items.GetEnumerator()) {
        if ($p.Value.status -eq "flattened" -and $p.Value.info_hash) { $hashesToDetach += [string]$p.Value.info_hash }
    }
}
if ($hashesToDetach.Count -gt 0) {
    Remove-HermesQbTorrentsKeepFiles $hashesToDetach $script:HermesQbFinishedLog | Out-Null
    Start-Sleep -Seconds 2
}
foreach ($root in $rootsToFlatten.Keys) {
    $result = Flatten-HermesShowRoot $root $script:HermesQbFinishedLog
    $totalFailed += [int]$result.failed
    $totalCollisions += [int]$result.collisions
    $totalMoved += [int]$result.copied
}

$scanTriggered = $false
if ($rootsToFlatten.Count -gt 0 -and ($totalMoved -gt 0 -or $totalCollisions -gt 0)) {
    $scanTriggered = Invoke-HermesPlexShowsRefresh $script:HermesQbFinishedLog
}

$mutex2 = New-Object System.Threading.Mutex($false, $script:HermesQbMutexName)
$hasLock2 = $false
try {
    $hasLock2 = $mutex2.WaitOne([TimeSpan]::FromSeconds(30))
    if ($hasLock2) {
        $reg2 = Read-HermesRegistry $script:HermesQbFinishedLog
        $toRemove = @()
        foreach ($p in $reg2.items.GetEnumerator()) {
            if ($p.Value.status -in @("flattened", "ignored")) { $toRemove += $p.Name }
        }
        foreach ($k in $toRemove) { $reg2.items.Remove($k) }
        if ($scanTriggered) { $reg2.last_scan_at = (Get-Date -Format "o") }
        if ($reg2.items.Count -eq 0) {
            $reg2.batch_started_at = $null
            $reg2.decision = [ordered]@{ event="cleared"; reason="all_items_flattened_or_ignored"; at=(Get-Date -Format "o") }
        }
        Write-HermesRegistry $reg2
    }
} catch {
    Log-HermesQb "  REGISTRY_CLEANUP_FAILED: $($_.Exception.Message)" $script:HermesQbFinishedLog
} finally {
    if ($hasLock2) { $mutex2.ReleaseMutex() | Out-Null }
    $mutex2.Dispose()
}

Log-HermesQb "=== Done roots=$($rootsToFlatten.Count) moved=$totalMoved failed=$totalFailed collisions_for_review=$totalCollisions scan_triggered=$scanTriggered ===" $script:HermesQbFinishedLog
