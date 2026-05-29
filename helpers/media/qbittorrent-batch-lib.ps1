# qbittorrent-batch-lib.ps1
# Shared smart batching/flattening helpers for qBittorrent hooks.

$script:HermesQbScriptDir = "C:\Users\santi\Documents\Hermes\Scripts"
$script:HermesQbStateFile = Join-Path $script:HermesQbScriptDir "qbittorrent-active.json"
$script:HermesQbFinishedLog = Join-Path $script:HermesQbScriptDir "qbittorrent-on-finished.log"
$script:HermesQbAddedLog = Join-Path $script:HermesQbScriptDir "qbittorrent-on-added.log"
$script:HermesQbMutexName = "Global\HermesQbittorrentBatchRegistry"
$script:HermesQbBase = if ($env:QBITTORRENT_BASE_URL) { $env:QBITTORRENT_BASE_URL } else { "http://localhost:8080/api/v2" }
$script:HermesQbUsername = $env:QBITTORRENT_USERNAME
$script:HermesQbPassword = $env:QBITTORRENT_PASSWORD
# Credentials are optional when qBittorrent is configured to bypass Web UI auth
# for Windows localhost. Invoke-HermesQbApi logs in only when both env vars exist.
$script:HermesQbWaitThresholdSeconds = 600
$script:HermesQbMinimumBatchSizeBytes = 2GB
$script:HermesQbMaxScanIntervalSeconds = 3600
$script:HermesQbExpectedSpeedBps = 2MB
$script:HermesQbPlexBase = "http://localhost:32400"
$script:HermesQbPlexShowsSection = "2"
$script:HermesQbPlexMoviesSection = "1"

$script:HermesReviewRoot = "D:\Review"
$script:HermesReviewCurrent = Join-Path $script:HermesReviewRoot "current"
$script:HermesReviewIndex = Join-Path $script:HermesReviewCurrent "review.yaml"

function ConvertTo-HermesYamlScalar([object]$Value) {
    if ($null -eq $Value) { return "null" }
    $s = [string]$Value
    if ($s -match '^[A-Za-z0-9_.:/\\ -]+$' -and $s -notmatch '^\s|\s$') { return $s }
    return '"' + ($s -replace '\\','\\' -replace '"','\"') + '"'
}

function Get-HermesReviewRunDir {
    $date = Get-Date -Format "yyyy-MM-dd"
    $time = Get-Date -Format "HH-mm-ss"
    $dir = Join-Path (Join-Path $script:HermesReviewRoot $date) $time
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    return $dir
}

function Get-HermesReviewItems {
    if (-not (Test-Path -LiteralPath $script:HermesReviewIndex)) { return @() }
    $items = @()
    $current = $null
    foreach ($line in (Get-Content -LiteralPath $script:HermesReviewIndex -ErrorAction SilentlyContinue)) {
        if ($line -match '^\s*-\s+id:\s*(.+?)\s*$') {
            if ($current) { $items += [pscustomobject]$current }
            $current = [ordered]@{ id = $Matches[1].Trim('"') }
        } elseif ($current -and $line -match '^\s+([A-Za-z0-9_]+):\s*(.*?)\s*$') {
            $k = $Matches[1]
            $v = $Matches[2].Trim()
            if ($v -eq 'null') { $v = $null }
            $v = $v.Trim('"')
            $current[$k] = $v
        }
    }
    if ($current) { $items += [pscustomobject]$current }
    return @($items)
}

function Write-HermesReviewIndex([array]$Items, [string]$Reason = "updated") {
    New-Item -ItemType Directory -Force -Path $script:HermesReviewCurrent | Out-Null
    $open = @($Items | Where-Object { $_.status -notin @('resolved_remote','resolved_local','resolved_merge','archived') })
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("# Wilson media conflict review queue")
    $lines.Add("# Edit decisions manually or run smart_org.bat for TUI decisions.")
    $lines.Add("updated_at: $(Get-Date -Format o)")
    $lines.Add("reason: $(ConvertTo-HermesYamlScalar $Reason)")
    $lines.Add("open_count: $($open.Count)")
    $lines.Add("review_root: D:\Review")
    $lines.Add("current: D:\Review\current")
    $lines.Add("choices:")
    $lines.Add("  remote: keep newly downloaded media already in the Plex library [default]")
    $lines.Add("  local: restore old/local media over the new file")
    $lines.Add("  merge: keep both with old/new filename prefixes")
    $lines.Add("items:")
    foreach ($item in @($Items | Sort-Object status, created_at)) {
        $lines.Add("  - id: $(ConvertTo-HermesYamlScalar $item.id)")
        foreach ($k in @('status','default_decision','media_type','kind','episode','title','show_root','library_path','old_review_path','old_archive_path','new_hash','old_hash','new_size_bytes','old_size_bytes','created_at','resolved_at','note')) {
            if ($item.PSObject.Properties.Name -contains $k) { $lines.Add("    ${k}: $(ConvertTo-HermesYamlScalar $item.$k)") }
        }
    }
    if ($Items.Count -eq 0) { $lines.Add("  []") }
    $text = ($lines -join "`r`n") + "`r`n"
    Set-Content -LiteralPath $script:HermesReviewIndex -Value $text -Encoding UTF8
}

function Add-HermesReviewItem {
    param(
        [string]$Kind,
        [string]$MediaType,
        [string]$Title,
        [string]$Episode,
        [string]$ShowRoot,
        [string]$LibraryPath,
        [string]$OldSourcePath,
        [string]$NewHash,
        [string]$OldHash,
        [int64]$NewSizeBytes,
        [int64]$OldSizeBytes,
        [string]$LogFile = $script:HermesQbFinishedLog
    )
    New-Item -ItemType Directory -Force -Path $script:HermesReviewCurrent | Out-Null
    $runDir = Get-HermesReviewRunDir
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $idRaw = "$LibraryPath|$OldSourcePath|$stamp"
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { $id = ([BitConverter]::ToString($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($idRaw))).Replace('-','').Substring(0,12).ToLowerInvariant()) }
    finally { $sha.Dispose() }
    $safeTitle = if ($Title) { $Title -replace '[\\/:*?"<>|]', '_' } else { 'media' }
    $safeEpisode = if ($Episode) { $Episode } else { 'item' }
    $destName = "${safeTitle}__${safeEpisode}__old__${id}$([System.IO.Path]::GetExtension($OldSourcePath))"
    $archivePath = Join-Path $runDir $destName
    $currentPath = Join-Path $script:HermesReviewCurrent $destName
    try {
        Move-Item -LiteralPath $OldSourcePath -Destination $archivePath -Force -ErrorAction Stop
        try { New-Item -ItemType HardLink -Path $currentPath -Target $archivePath -ErrorAction Stop | Out-Null }
        catch { Copy-Item -LiteralPath $archivePath -Destination $currentPath -Force -ErrorAction Stop }
    } catch {
        Log-HermesQb "  REVIEW_QUEUE_FAILED: $OldSourcePath -> $archivePath | $($_.Exception.Message)" $LogFile
        return $null
    }
    $items = @(Get-HermesReviewItems)
    $item = [pscustomobject][ordered]@{
        id = $id
        status = 'open'
        default_decision = 'remote'
        media_type = $MediaType
        kind = $Kind
        episode = $Episode
        title = $Title
        show_root = $ShowRoot
        library_path = $LibraryPath
        old_review_path = $currentPath
        old_archive_path = $archivePath
        new_hash = $NewHash
        old_hash = $OldHash
        new_size_bytes = $NewSizeBytes
        old_size_bytes = $OldSizeBytes
        created_at = (Get-Date -Format o)
        note = 'Remote/new media is currently kept in the Plex library. Local/old media is staged for review.'
    }
    $items += $item
    Write-HermesReviewIndex $items "added_review_item"
    return $item
}

function Set-HermesReviewItemStatus([string]$Id, [string]$Status, [string]$Note = $null) {
    $items = @(Get-HermesReviewItems)
    foreach ($item in $items) {
        if ($item.id -eq $Id) {
            $item.status = $Status
            $item.resolved_at = (Get-Date -Format o)
            if ($Note) { $item.note = $Note }
        }
    }
    Write-HermesReviewIndex $items "resolved_$Status"
}

function Invoke-HermesReviewTui([string]$LogFile = $script:HermesQbFinishedLog) {
    $items = @(Get-HermesReviewItems | Where-Object { $_.status -eq 'open' })
    if ($items.Count -eq 0) {
        Write-Host "No open Wilson review items."
        Write-HermesReviewIndex @(Get-HermesReviewItems) "tui_no_open_items"
        return
    }
    foreach ($item in $items) {
        Clear-Host
        Write-Host "Wilson Review Queue" -ForegroundColor Cyan
        Write-Host "ID: $($item.id)"
        Write-Host "Title: $($item.title)  Episode: $($item.episode)"
        Write-Host "New/remote currently in library:" -ForegroundColor Green
        Write-Host "  $($item.library_path)"
        Write-Host "Old/local staged for review:" -ForegroundColor Yellow
        Write-Host "  $($item.old_review_path)"
        Write-Host ""
        $choice = Read-Host "Decision [R]emote default / [L]ocal / [M]erge / [S]kip"
        if ([string]::IsNullOrWhiteSpace($choice)) { $choice = 'R' }
        switch -Regex ($choice.ToUpperInvariant()) {
            '^L' {
                try {
                    $lib = [string]$item.library_path
                    if (Test-Path -LiteralPath $lib) {
                        $replacedDir = Join-Path (Split-Path -Parent ([string]$item.old_archive_path)) "replaced_remote"
                        New-Item -ItemType Directory -Force -Path $replacedDir | Out-Null
                        Move-Item -LiteralPath $lib -Destination (Join-Path $replacedDir (Split-Path -Leaf $lib)) -Force -ErrorAction Stop
                    }
                    Copy-Item -LiteralPath ([string]$item.old_archive_path) -Destination $lib -Force -ErrorAction Stop
                    Set-HermesReviewItemStatus $item.id 'resolved_local' 'User chose local/old; old media restored over remote/new and remote/new archived.'
                    Log-HermesQb "  REVIEW_DECISION local | id=$($item.id) | $lib" $LogFile
                } catch { Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red; Start-Sleep -Seconds 3 }
            }
            '^M' {
                try {
                    $lib = [string]$item.library_path
                    $dir = Split-Path -Parent $lib
                    $leaf = Split-Path -Leaf $lib
                    $newPath = Join-Path $dir ("new - $leaf")
                    $oldPath = Join-Path $dir ("old - $leaf")
                    if (Test-Path -LiteralPath $lib) { Move-Item -LiteralPath $lib -Destination $newPath -Force -ErrorAction Stop }
                    Copy-Item -LiteralPath ([string]$item.old_archive_path) -Destination $oldPath -Force -ErrorAction Stop
                    Set-HermesReviewItemStatus $item.id 'resolved_merge' 'User chose merge; both old and new copies kept in library with prefixes.'
                    Log-HermesQb "  REVIEW_DECISION merge | id=$($item.id) | $dir" $LogFile
                } catch { Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red; Start-Sleep -Seconds 3 }
            }
            '^S' { continue }
            default {
                Set-HermesReviewItemStatus $item.id 'resolved_remote' 'User chose remote/new or accepted default; old media remains archived in review.'
                Log-HermesQb "  REVIEW_DECISION remote | id=$($item.id)" $LogFile
            }
        }
    }
}

function Log-HermesQb([string]$Message, [string]$LogFile = $script:HermesQbFinishedLog) {
    New-Item -ItemType Directory -Force -Path $script:HermesQbScriptDir | Out-Null
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -LiteralPath $LogFile -Value "$ts | $Message" -Encoding UTF8
}

function Get-HermesRegistryKey([string]$Name, [string]$Path, [string]$Hash) {
    if (-not [string]::IsNullOrWhiteSpace($Hash) -and $Hash -ne "%I") {
        return ("ih_" + ($Hash.Trim().ToLowerInvariant() -replace '[^a-f0-9]', ''))
    }
    $raw = "$Name|$Path"
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($raw)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return ("legacy_" + ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace("-", "").Substring(0, 16).ToLowerInvariant()) }
    finally { $sha.Dispose() }
}

function Get-HermesMediaType([string]$Category, [string]$SavePath, [string]$ContentPath) {
    $c = if ($Category) { $Category.Trim().ToLowerInvariant() } else { "" }
    if ($c -in @("tv", "show", "shows", "series")) { return "show" }
    if ($c -in @("movie", "movies", "film", "films")) { return "movie" }
    if ($c -eq "music") { return "music" }
    foreach ($p in @($ContentPath, $SavePath)) {
        if ([string]::IsNullOrWhiteSpace($p)) { continue }
        if ($p -match '^D:\\Shows(\\|$)') { return "show" }
        if ($p -match '^D:\\Movies(\\|$)') { return "movie" }
        if ($p -match '^D:\\Music(\\|$)') { return "music" }
    }
    return "unknown"
}

function New-HermesRegistry {
    return [ordered]@{
        schema_version = 3
        batch_started_at = (Get-Date -Format "o")
        updated_at = (Get-Date -Format "o")
        last_scan_at = $null
        decision = $null
        items = [ordered]@{}
    }
}

function Resolve-HermesShowRoot($Item) {
    $candidates = @()
    if ($Item.content_path) { $candidates += [string]$Item.content_path }
    if ($Item.save_path) { $candidates += [string]$Item.save_path }
    foreach ($candidate in $candidates) {
        if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
        if ($candidate -notmatch '^D:\\Shows(\\|$)') { continue }
        try {
            $p = $candidate.TrimEnd("\")
            $showsRoot = "D:\Shows"
            if ($p -ieq $showsRoot) { continue }
            if ($p -notlike "$showsRoot\*") { continue }
            $relative = $p.Substring($showsRoot.Length).TrimStart("\")
            if ([string]::IsNullOrWhiteSpace($relative)) { continue }
            $first = ($relative -split '\\')[0]
            if (-not [string]::IsNullOrWhiteSpace($first)) { return (Join-Path $showsRoot $first) }
        } catch {}
    }
    return $null
}


function Resolve-HermesMovieRoot($Item) {
    $candidates = @()
    if ($Item.content_path) { $candidates += [string]$Item.content_path }
    if ($Item.save_path) { $candidates += [string]$Item.save_path }
    foreach ($candidate in $candidates) {
        if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
        if ($candidate -notmatch '^D:\\Movies(\\|$)') { continue }
        try {
            $p = $candidate.TrimEnd("\")
            $moviesRoot = "D:\Movies"
            if ($p -ieq $moviesRoot) { continue }
            if ($p -notlike "$moviesRoot\*") { continue }
            $relative = $p.Substring($moviesRoot.Length).TrimStart("\")
            if ([string]::IsNullOrWhiteSpace($relative)) { continue }
            $first = ($relative -split '\\')[0]
            if (-not [string]::IsNullOrWhiteSpace($first)) { return (Join-Path $moviesRoot $first) }
        } catch {}
    }
    return $null
}

function New-HermesRegistryItem([string]$Name, [string]$ContentPath, [string]$SavePath, [string]$InfoHash, [string]$Category, [string]$Status = "active") {
    $mediaType = Get-HermesMediaType $Category $SavePath $ContentPath
    $item = [ordered]@{
        name = $Name
        info_hash = $InfoHash
        category = $Category
        media_type = $mediaType
        save_path = $SavePath
        content_path = $ContentPath
        show_root = $null
        added_at = (Get-Date -Format "o")
        finished_at = $null
        status = $Status
        size_bytes = 0
        completed_bytes = 0
        remaining_bytes = 0
        progress = 0.0
        download_speed_bps = 0
        qb_eta_seconds = -1
        computed_eta_seconds = -1
        effective_eta_seconds = -1
        seeds = 0
        peers = 0
        availability = $null
        reliability_score = 0.0
        priority_rank = 9999
        eta_group = "unknown"
        last_seen_at = $null
        last_ranked_at = $null
        stale = $false
    }
    $item.show_root = Resolve-HermesShowRoot $item
    return $item
}

function Read-HermesRegistry([string]$LogFile = $script:HermesQbFinishedLog) {
    if (-not (Test-Path -LiteralPath $script:HermesQbStateFile)) { return (New-HermesRegistry) }
    $raw = Get-Content -LiteralPath $script:HermesQbStateFile -Raw -ErrorAction SilentlyContinue
    if ([string]::IsNullOrWhiteSpace($raw)) { return (New-HermesRegistry) }
    try { $parsed = $raw | ConvertFrom-Json } catch {
        Log-HermesQb "REGISTRY_READ_FAILED: $($_.Exception.Message); resetting registry" $LogFile
        return (New-HermesRegistry)
    }

    $reg = New-HermesRegistry
    if ($parsed.batch_started_at) { $reg.batch_started_at = [string]$parsed.batch_started_at }
    if ($parsed.last_scan_at) { $reg.last_scan_at = [string]$parsed.last_scan_at }
    if ($parsed.decision) { $reg.decision = $parsed.decision }

    if ($parsed.items) {
        foreach ($p in $parsed.items.PSObject.Properties) {
            $v = $p.Value
            $key = $p.Name
            if (-not $key) { $key = Get-HermesRegistryKey $v.name $v.save_path $v.info_hash }
            $status = if ($v.status) { [string]$v.status } else { "active" }
            $item = New-HermesRegistryItem ([string]$v.name) ([string]$v.content_path) ([string]$v.save_path) ([string]$v.info_hash) ([string]$v.category) $status
            foreach ($prop in @('added_at','finished_at','size_bytes','completed_bytes','remaining_bytes','progress','download_speed_bps','qb_eta_seconds','computed_eta_seconds','effective_eta_seconds','seeds','peers','availability','reliability_score','priority_rank','eta_group','last_seen_at','last_ranked_at','stale')) {
                if ($null -ne $v.$prop) { $item[$prop] = $v.$prop }
            }
            if ($v.media_type) { $item.media_type = [string]$v.media_type }
            if ($v.show_root) { $item.show_root = [string]$v.show_root } else { $item.show_root = Resolve-HermesShowRoot $item }
            $reg.items[$key] = $item
        }
    }
    return $reg
}

function Write-HermesRegistry($Registry) {
    New-Item -ItemType Directory -Force -Path $script:HermesQbScriptDir | Out-Null
    $Registry.schema_version = 3
    $Registry.updated_at = (Get-Date -Format "o")
    $Registry | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $script:HermesQbStateFile -Encoding UTF8
}

function Invoke-HermesQbApi([string]$Endpoint, [hashtable]$Body = $null) {
    $useAuth = -not [string]::IsNullOrWhiteSpace($script:HermesQbUsername) -and -not [string]::IsNullOrWhiteSpace($script:HermesQbPassword)
    $session = $null
    if ($useAuth) {
        $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
        Invoke-WebRequest -Uri "$script:HermesQbBase/auth/login" -Method POST -Body @{username=$script:HermesQbUsername; password=$script:HermesQbPassword} -WebSession $session -UseBasicParsing -ErrorAction Stop | Out-Null
    }
    if ($Body) {
        if ($useAuth) { return Invoke-WebRequest -Uri "$script:HermesQbBase/$Endpoint" -Method POST -Body $Body -WebSession $session -UseBasicParsing -ErrorAction Stop }
        return Invoke-WebRequest -Uri "$script:HermesQbBase/$Endpoint" -Method POST -Body $Body -UseBasicParsing -ErrorAction Stop
    }
    if ($useAuth) { return Invoke-WebRequest -Uri "$script:HermesQbBase/$Endpoint" -WebSession $session -UseBasicParsing -ErrorAction Stop }
    return Invoke-WebRequest -Uri "$script:HermesQbBase/$Endpoint" -UseBasicParsing -ErrorAction Stop
}

function Get-HermesQbTorrents([string]$LogFile = $script:HermesQbFinishedLog) {
    try {
        $r = Invoke-HermesQbApi "torrents/info"
        return @($r.Content | ConvertFrom-Json)
    } catch {
        Log-HermesQb "QB_API_FAILED: $($_.Exception.Message)" $LogFile
        return @()
    }
}

function Get-HermesReliabilityScore($Torrent, [long]$SpeedBps) {
    $seeds = 0.0
    if ($null -ne $Torrent.num_seeds) { $seeds = [double]$Torrent.num_seeds }
    $peers = 0.0
    if ($null -ne $Torrent.num_leechs) { $peers = [double]$Torrent.num_leechs }
    $availability = if ($null -ne $Torrent.availability -and [double]$Torrent.availability -ge 0) { [Math]::Min([double]$Torrent.availability, 1.0) } else { 0.5 }
    $seedScore = [Math]::Min($seeds / 20.0, 1.0)
    $peerScore = [Math]::Min(($seeds + $peers) / 50.0, 1.0)
    $speedScore = [Math]::Min(([double]$SpeedBps) / ([double]$script:HermesQbExpectedSpeedBps), 1.0)
    return [Math]::Round((0.35*$seedScore + 0.20*$peerScore + 0.25*$availability + 0.20*$speedScore), 3)
}

function Get-HermesEtaGroup([double]$Progress, [int64]$Eta, [double]$Reliability, [int64]$Speed, [int]$Seeds) {
    if ($Progress -ge 0.999) { return "ready_now" }
    if ($Speed -le 0 -and $Seeds -le 0) { return "stalled" }
    if ($Eta -ge 0 -and $Eta -le 600 -and $Reliability -ge 0.45) { return "near" }
    if ($Eta -ge 0 -and $Eta -le 2700 -and $Reliability -ge 0.35) { return "medium" }
    if ($Eta -lt 0) { return "unknown_slow" }
    return "long_tail"
}

function Update-HermesRegistryTelemetry($Registry, [array]$Torrents, [string]$LogFile = $script:HermesQbFinishedLog) {
    $byHash = @{}
    foreach ($t in $Torrents) {
        if ($t.hash) { $byHash[[string]$t.hash.ToLowerInvariant()] = $t }
    }
    $now = Get-Date -Format "o"
    foreach ($p in $Registry.items.GetEnumerator()) {
        $item = $p.Value
        $hash = if ($item.info_hash) { [string]$item.info_hash.ToLowerInvariant() } else { "" }
        if ($hash -and $byHash.ContainsKey($hash)) {
            $t = $byHash[$hash]
            $item.name = [string]$t.name
            $item.category = [string]$t.category
            $item.save_path = [string]$t.save_path
            $item.content_path = [string]$t.content_path
            $item.media_type = Get-HermesMediaType $item.category $item.save_path $item.content_path
            $item.show_root = Resolve-HermesShowRoot $item
            $size = 0L
            if ($null -ne $t.size) { $size = [int64]$t.size }
            $progress = 0.0
            if ($null -ne $t.progress) { $progress = [double]$t.progress }
            $completed = [int64]($progress * $size)
            if ($null -ne $t.completed) { $completed = [int64]$t.completed }
            $speed = 0L
            if ($null -ne $t.dlspeed) { $speed = [int64]$t.dlspeed }
            $remaining = [Math]::Max([int64]0, $size - $completed)
            $qbEta = -1L
            if ($null -ne $t.eta) { $qbEta = [int64]$t.eta }
            $computedEta = if ($remaining -le 0) { 0 } elseif ($speed -gt 0) { [int64][Math]::Ceiling($remaining / [double]$speed) } else { -1 }
            $rel = Get-HermesReliabilityScore $t $speed
            $effectiveEta = if ($progress -ge 0.999) { 0 } elseif ($qbEta -ge 0 -and $computedEta -ge 0) { [int64][Math]::Round(($qbEta*0.6) + ($computedEta*0.4)) } elseif ($qbEta -ge 0) { $qbEta } elseif ($computedEta -ge 0) { $computedEta } else { -1 }
            if ($effectiveEta -gt 604800) { $effectiveEta = 604800 }
            $item.size_bytes = $size
            $item.completed_bytes = $completed
            $item.remaining_bytes = $remaining
            $item.progress = [Math]::Round($progress, 5)
            $item.download_speed_bps = $speed
            $item.qb_eta_seconds = $qbEta
            $item.computed_eta_seconds = $computedEta
            $item.effective_eta_seconds = $effectiveEta
            $item.seeds = 0
            if ($null -ne $t.num_seeds) { $item.seeds = [int]$t.num_seeds }
            $item.peers = 0
            if ($null -ne $t.num_leechs) { $item.peers = [int]$t.num_leechs }
            $item.availability = if ($null -ne $t.availability) { [double]$t.availability } else { $null }
            $item.reliability_score = $rel
            $item.eta_group = Get-HermesEtaGroup $progress $effectiveEta $rel $speed $item.seeds
            $item.last_seen_at = $now
            $item.last_ranked_at = $now
            $item.stale = $false
            if ($item.media_type -eq "show" -and $progress -ge 0.999 -and $item.status -eq "active") {
                $item.status = "finished"
                $item.finished_at = $now
            }
        } else {
            $item.stale = $true
        }
    }

    $rank = 1
    $ranked = @($Registry.items.GetEnumerator() | Sort-Object @{Expression={ if ($_.Value.effective_eta_seconds -lt 0) { 999999999 } else { [int64]$_.Value.effective_eta_seconds } }}, @{Expression={ [int64]$_.Value.size_bytes }})
    foreach ($p in $ranked) {
        $p.Value.priority_rank = $rank
        $rank++
    }
    return $Registry
}

function Get-HermesFlushDecision($Registry) {
    $finished = @()
    $active = @()
    foreach ($p in $Registry.items.GetEnumerator()) {
        $v = $p.Value
        if ($v.media_type -ne "show") { continue }
        if ($v.status -eq "finished") { $finished += $v }
        elseif ($v.status -eq "active") { $active += $v }
    }
    $finishedBytes = [int64]0
    foreach ($f in $finished) { $finishedBytes += [int64]$f.size_bytes }
    $reason = "none"
    $shouldFlush = $false

    if ($finished.Count -eq 0) {
        $reason = "no_finished_candidates"
    } elseif ($active.Count -eq 0) {
        $shouldFlush = $true; $reason = "all_registered_items_finished"
    } elseif ($finishedBytes -ge [int64]$script:HermesQbMinimumBatchSizeBytes) {
        $shouldFlush = $true; $reason = "finished_batch_size_threshold"
    } else {
        $allNear = $true
        $maxEta = 0
        foreach ($a in $active) {
            $eta = [int64]$a.effective_eta_seconds
            if ($eta -lt 0) { $allNear = $false }
            if ($eta -gt $maxEta) { $maxEta = $eta }
            if (-not ($a.eta_group -eq "near" -and [double]$a.reliability_score -ge 0.45)) { $allNear = $false }
        }
        if ($allNear -and $maxEta -le $script:HermesQbWaitThresholdSeconds) {
            $shouldFlush = $false; $reason = "waiting_for_near_reliable_active_items"
        } else {
            $shouldFlush = $true; $reason = "active_items_are_medium_long_tail_or_stalled"
        }
    }

    return [ordered]@{
        should_flush = $shouldFlush
        reason = $reason
        finished_count = $finished.Count
        active_count = $active.Count
        finished_bytes = $finishedBytes
        active = @($active | ForEach-Object { [ordered]@{ name=$_.name; eta=$_.effective_eta_seconds; group=$_.eta_group; reliability=$_.reliability_score; progress=$_.progress } })
        finished = @($finished | ForEach-Object { [ordered]@{ name=$_.name; root=$_.show_root; size_bytes=$_.size_bytes } })
    }
}

function Remove-HermesQbTorrentsKeepFiles([string[]]$Hashes, [string]$LogFile = $script:HermesQbFinishedLog) {
    $clean = @($Hashes | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
    if ($clean.Count -eq 0) { return $false }
    try {
        Invoke-HermesQbApi "torrents/delete" @{ hashes = ($clean -join '|'); deleteFiles = "false" } | Out-Null
        Log-HermesQb "  qBittorrent removed completed torrent(s), keeping files: count=$($clean.Count)" $LogFile
        return $true
    } catch {
        Log-HermesQb "  qBittorrent remove-keep-files failed: $($_.Exception.Message)" $LogFile
        return $false
    }
}

function Get-HermesCleanFileName([string]$Name) {
    $clean = $Name
    # Strip explicit tracker domains, but do not treat release-group names before
    # normal sidecar extensions as domains. Example: `Movie-RARBG.idx` must keep
    # `.idx`; older pattern matched `RARBG.idx` and produced an extensionless
    # sidecar collision during movie flattening.
    $clean = $clean -replace '(?i)(?:https?://\S+|www\.[a-z0-9][a-z0-9\-]*(?:\.[a-z0-9][a-z0-9\-]*)+\b|(?:eztvx?|uindex|torrentgalaxy|tgx|torrentcouch)\.[a-z]{2,}\b)(?:\s*[-_.]\s*)?', ''
    $clean = $clean -replace '\[.*?\]', ''
    $clean = $clean -replace '[ _.-]{3,}', ' '
    $clean = $clean -replace '\s+', ' '
    $clean = $clean.Trim(' ', '.', '-', '_')
    if ([string]::IsNullOrWhiteSpace($clean)) { return $Name }
    return $clean
}

function Get-HermesSeasonFolderName([string]$ShowRoot, [int]$SeasonNumber) {
    $existing = Get-ChildItem -LiteralPath $ShowRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "^Season\s+$SeasonNumber\s+\(\d{4}\)$" } | Select-Object -First 1
    if ($existing) { return $existing.Name }
    $showYear = $null
    if ((Split-Path -Leaf $ShowRoot) -match '\((\d{4})\)$') { $showYear = $Matches[1] }
    if ($showYear) { return "Season $SeasonNumber ($showYear)" }
    return "Season $SeasonNumber"
}

function Get-HermesFileHashSafe([string]$Path, [string]$LogFile = $script:HermesQbFinishedLog) {
    try { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant() }
    catch { Log-HermesQb "  HASH FAILED: $Path | $($_.Exception.Message)" $LogFile; return $null }
}

function Get-HermesCollisionPath([string]$Destination, [string]$SourceHash) {
    $dir = Split-Path -Parent $Destination
    $base = [System.IO.Path]::GetFileNameWithoutExtension($Destination)
    $ext = [System.IO.Path]::GetExtension($Destination)
    $shortHash = if ($SourceHash) { $SourceHash.Substring(0, [Math]::Min(12, $SourceHash.Length)) } else { "unhashed" }
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    for ($i = 1; $i -le 999; $i++) {
        $suffix = "__COLLISION_REVIEW_${stamp}_${shortHash}"
        if ($i -gt 1) { $suffix = "${suffix}_$i" }
        $candidate = Join-Path $dir ("$base$suffix$ext")
        if (-not (Test-Path -LiteralPath $candidate)) { return $candidate }
    }
    throw "Could not allocate collision review path for $Destination"
}

function Flatten-HermesShowRoot([string]$ShowRoot, [string]$LogFile = $script:HermesQbFinishedLog) {
    if ([string]::IsNullOrWhiteSpace($ShowRoot) -or $ShowRoot.TrimEnd("\") -ieq "D:\Shows") {
        Log-HermesQb "  SKIP: unsafe show root $ShowRoot" $LogFile
        return @{ copied = 0; deleted = 0; failed = 1; dirsRemoved = 0; seasons = 0; collisions = 0 }
    }
    if (-not (Test-Path -LiteralPath $ShowRoot -PathType Container)) {
        Log-HermesQb "  SKIP: $ShowRoot missing" $LogFile
        return @{ copied = 0; deleted = 0; failed = 1; dirsRemoved = 0; seasons = 0; collisions = 0 }
    }

    Log-HermesQb "  Show root: $ShowRoot" $LogFile
    $epRegex = "[Ss](\d{1,2})[ ._\-]*[Ee]\d{1,2}"
    $mediaExts = @(".mkv", ".mp4", ".avi", ".m4v", ".wmv")
    $sidecarExts = @(".srt", ".sub", ".idx", ".ass", ".ssa", ".vtt", ".nfo")
    $copied = 0; $deleted = 0; $failed = 0; $dirsRemoved = 0; $collisions = 0
    $seasonDirs = @{}
    $epBaseNames = @{}
    $allFiles = Get-ChildItem -LiteralPath $ShowRoot -File -Recurse -Depth 7 -ErrorAction SilentlyContinue

    foreach ($f in $allFiles) {
        $ext = $f.Extension.ToLowerInvariant()
        if ($ext -in $mediaExts -and $f.Name -match $epRegex) { $epBaseNames[$f.BaseName] = [int]$Matches[1] }
    }

    foreach ($f in $allFiles) {
        $sn = $null
        $fileExt = $f.Extension.ToLowerInvariant()
        if ($fileExt -in $mediaExts -and $f.Name -match $epRegex) { $sn = [int]$Matches[1] }
        elseif ($fileExt -in $sidecarExts) {
            foreach ($b in $epBaseNames.Keys) { if ($f.BaseName.StartsWith($b)) { $sn = $epBaseNames[$b]; break } }
        }
        if ($null -eq $sn) { continue }
        $season = Get-HermesSeasonFolderName $ShowRoot $sn
        $td = Join-Path $ShowRoot $season
        if ($f.DirectoryName.TrimEnd("\") -ieq $td.TrimEnd("\")) { continue }
        if (-not $seasonDirs.ContainsKey($season)) { New-Item -ItemType Directory -Force -Path $td | Out-Null; $seasonDirs[$season] = $true }
        $dest = Join-Path $td (Get-HermesCleanFileName $f.Name)
        if (Test-Path -LiteralPath $dest) {
            try {
                $destItem = Get-Item -LiteralPath $dest -ErrorAction Stop
                $srcItem = Get-Item -LiteralPath $f.FullName -ErrorAction Stop
                if ($destItem.Length -eq $srcItem.Length) {
                    $destHash = Get-HermesFileHashSafe $dest $LogFile
                    $srcHash = Get-HermesFileHashSafe $f.FullName $LogFile
                    if ($destHash -and $srcHash -and $destHash -eq $srcHash) {
                        Remove-Item -LiteralPath $f.FullName -Force -ErrorAction Stop
                        Log-HermesQb "  DUPLICATE REMOVED: $($f.FullName) matches $dest" $LogFile
                        $deleted++
                        continue
                    }
                }
                $srcReviewHash = Get-HermesFileHashSafe $f.FullName $LogFile
                $destHash = Get-HermesFileHashSafe $dest $LogFile
                $epCode = $null
                if ($f.Name -match '[Ss](\d{1,2})[ ._\-]*[Ee](\d{1,2})') { $epCode = ('S{0:D2}E{1:D2}' -f [int]$Matches[1], [int]$Matches[2]) }
                $title = Split-Path -Leaf $ShowRoot
                $reviewItem = Add-HermesReviewItem -Kind 'episode_collision' -MediaType 'show' -Title $title -Episode $epCode -ShowRoot $ShowRoot -LibraryPath $dest -OldSourcePath $dest -NewHash $srcReviewHash -OldHash $destHash -NewSizeBytes $srcItem.Length -OldSizeBytes $destItem.Length -LogFile $LogFile
                Move-Item -LiteralPath $f.FullName -Destination $dest -Force -ErrorAction Stop
                $deleted++
                Log-HermesQb "  COLLISION DEFAULT_REMOTE: kept_new=$dest queued_old=$($reviewItem.old_review_path) | source=$($f.FullName)" $LogFile
                $copied++; $collisions++
                continue
            } catch {
                Log-HermesQb "  COLLISION HANDLING FAILED: $($f.FullName) -> $dest | $($_.Exception.Message)" $LogFile
                $failed++
                continue
            }
        }
        try {
            Move-Item -LiteralPath $f.FullName -Destination $dest -ErrorAction Stop
            $copied++
            $deleted++
        } catch {
            Log-HermesQb "  MOVE FAILED: $($f.FullName) -> $dest | $($_.Exception.Message)" $LogFile
            $failed++
        }
    }

    $keep = @{ $ShowRoot = $true }
    foreach ($s in $seasonDirs.Keys) { $keep[(Join-Path $ShowRoot $s)] = $true }
    Get-ChildItem -LiteralPath $ShowRoot -Directory -Recurse -Depth 7 -ErrorAction SilentlyContinue | Sort-Object { $_.FullName.Length } -Descending | ForEach-Object {
        if (-not $keep.ContainsKey($_.FullName)) {
            if ((Get-ChildItem -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue).Count -eq 0) {
                Remove-Item -LiteralPath $_.FullName -Force -Recurse -ErrorAction SilentlyContinue
                $dirsRemoved++
            }
        }
    }
    Log-HermesQb "  copied_or_moved=$copied removed_original_or_duplicate=$deleted failed=$failed collisions_for_review=$collisions empty_dirs_removed=$dirsRemoved seasons=$($seasonDirs.Count)" $LogFile
    return @{ copied = $copied; deleted = $deleted; failed = $failed; dirsRemoved = $dirsRemoved; seasons = $seasonDirs.Count; collisions = $collisions }
}


function Flatten-HermesMovieRoot([string]$MovieRoot, [string]$LogFile = $script:HermesQbFinishedLog) {
    if ([string]::IsNullOrWhiteSpace($MovieRoot) -or $MovieRoot.TrimEnd("\") -ieq "D:\Movies") {
        Log-HermesQb "  MOVIE SKIP: unsafe movie root $MovieRoot" $LogFile
        return @{ moved = 0; deleted = 0; failed = 1; collisions = 0; dirsRemoved = 0 }
    }
    if (-not (Test-Path -LiteralPath $MovieRoot -PathType Container)) {
        Log-HermesQb "  MOVIE SKIP: $MovieRoot missing" $LogFile
        return @{ moved = 0; deleted = 0; failed = 1; collisions = 0; dirsRemoved = 0 }
    }
    Log-HermesQb "  Movie root: $MovieRoot" $LogFile
    $mediaExts = @(".mkv", ".mp4", ".avi", ".m4v", ".wmv", ".mov")
    $sidecarExts = @(".srt", ".sub", ".idx", ".ass", ".ssa", ".vtt", ".nfo")
    $moved = 0; $deleted = 0; $failed = 0; $collisions = 0; $dirsRemoved = 0
    $allFiles = Get-ChildItem -LiteralPath $MovieRoot -File -Recurse -Depth 7 -ErrorAction SilentlyContinue
    $movieBases = @{}
    foreach ($f in $allFiles) {
        if ($f.Extension.ToLowerInvariant() -in $mediaExts) { $movieBases[$f.BaseName] = $true }
    }
    foreach ($f in $allFiles) {
        $ext = $f.Extension.ToLowerInvariant()
        $isMedia = $ext -in $mediaExts
        $isSidecar = $false
        if (-not $isMedia -and $ext -in $sidecarExts) {
            foreach ($b in $movieBases.Keys) { if ($f.BaseName.StartsWith($b)) { $isSidecar = $true; break } }
        }
        if (-not ($isMedia -or $isSidecar)) { continue }
        if ($f.DirectoryName.TrimEnd("\") -ieq $MovieRoot.TrimEnd("\")) { continue }
        $dest = Join-Path $MovieRoot (Get-HermesCleanFileName $f.Name)
        if (Test-Path -LiteralPath $dest) {
            try {
                $destItem = Get-Item -LiteralPath $dest -ErrorAction Stop
                $srcItem = Get-Item -LiteralPath $f.FullName -ErrorAction Stop
                if ($destItem.Length -eq $srcItem.Length) {
                    $destHash = Get-HermesFileHashSafe $dest $LogFile
                    $srcHash = Get-HermesFileHashSafe $f.FullName $LogFile
                    if ($destHash -and $srcHash -and $destHash -eq $srcHash) {
                        Remove-Item -LiteralPath $f.FullName -Force -ErrorAction Stop
                        Log-HermesQb "  MOVIE DUPLICATE REMOVED: $($f.FullName) matches $dest" $LogFile
                        $deleted++
                        continue
                    }
                }
                $srcReviewHash = Get-HermesFileHashSafe $f.FullName $LogFile
                $destHash = Get-HermesFileHashSafe $dest $LogFile
                $title = Split-Path -Leaf $MovieRoot
                $reviewItem = Add-HermesReviewItem -Kind 'movie_collision' -MediaType 'movie' -Title $title -Episode $null -ShowRoot $MovieRoot -LibraryPath $dest -OldSourcePath $dest -NewHash $srcReviewHash -OldHash $destHash -NewSizeBytes $srcItem.Length -OldSizeBytes $destItem.Length -LogFile $LogFile
                Move-Item -LiteralPath $f.FullName -Destination $dest -Force -ErrorAction Stop
                Log-HermesQb "  MOVIE COLLISION DEFAULT_REMOTE: kept_new=$dest queued_old=$($reviewItem.old_review_path) | source=$($f.FullName)" $LogFile
                $moved++; $deleted++; $collisions++
                continue
            } catch {
                Log-HermesQb "  MOVIE COLLISION HANDLING FAILED: $($f.FullName) -> $dest | $($_.Exception.Message)" $LogFile
                $failed++
                continue
            }
        }
        try {
            Move-Item -LiteralPath $f.FullName -Destination $dest -ErrorAction Stop
            $moved++; $deleted++
        } catch {
            $moveError = $_.Exception.Message
            try {
                Copy-Item -LiteralPath $f.FullName -Destination $dest -Force -ErrorAction Stop
                $moved++
                try { Remove-Item -LiteralPath $f.FullName -Force -ErrorAction Stop; $deleted++ }
                catch { Log-HermesQb "  MOVIE SOURCE REMOVE DEFERRED: $($f.FullName) | $($_.Exception.Message)" $LogFile }
            } catch {
                Log-HermesQb "  MOVIE MOVE FAILED: $($f.FullName) -> $dest | move=$moveError | copy=$($_.Exception.Message)" $LogFile
                $failed++
            }
        }
    }
    Get-ChildItem -LiteralPath $MovieRoot -Directory -Recurse -Depth 7 -ErrorAction SilentlyContinue | Sort-Object { $_.FullName.Length } -Descending | ForEach-Object {
        if ((Get-ChildItem -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue).Count -eq 0) {
            Remove-Item -LiteralPath $_.FullName -Force -Recurse -ErrorAction SilentlyContinue
            $dirsRemoved++
        }
    }
    Log-HermesQb "  movie_moved=$moved removed_original_or_duplicate=$deleted failed=$failed collisions_for_review=$collisions empty_dirs_removed=$dirsRemoved" $LogFile
    return @{ moved = $moved; deleted = $deleted; failed = $failed; collisions = $collisions; dirsRemoved = $dirsRemoved }
}

function Invoke-HermesPlexMoviesRefresh([string]$LogFile = $script:HermesQbFinishedLog) {
    $token = $env:PLEX_TOKEN
    if ([string]::IsNullOrWhiteSpace($token)) {
        try { $token = (Get-ItemProperty -Path "HKCU:\Software\Plex, Inc.\Plex Media Server" -Name "PlexOnlineToken" -ErrorAction Stop).PlexOnlineToken } catch { $token = $null }
    }
    if ([string]::IsNullOrWhiteSpace($token)) { Log-HermesQb "  Plex Movies SKIPPED: no token found" $LogFile; return $false }
    try {
        Log-HermesQb "  Plex refresh movies section $script:HermesQbPlexMoviesSection..." $LogFile
        $r = Invoke-WebRequest -UseBasicParsing -Uri "$script:HermesQbPlexBase/library/sections/$script:HermesQbPlexMoviesSection/refresh" -Method Get -TimeoutSec 30 -Headers @{"X-Plex-Token"=$token}
        Log-HermesQb "  Plex Movies: HTTP $($r.StatusCode)" $LogFile
        return $true
    } catch {
        Log-HermesQb "  Plex Movies FAILED: $($_.Exception.Message)" $LogFile
        return $false
    }
}

function Invoke-HermesPlexShowsRefresh([string]$LogFile = $script:HermesQbFinishedLog) {
    $token = $env:PLEX_TOKEN
    if ([string]::IsNullOrWhiteSpace($token)) {
        try { $token = (Get-ItemProperty -Path "HKCU:\Software\Plex, Inc.\Plex Media Server" -Name "PlexOnlineToken" -ErrorAction Stop).PlexOnlineToken } catch { $token = $null }
    }
    if ([string]::IsNullOrWhiteSpace($token)) { Log-HermesQb "  Plex SKIPPED: no token found" $LogFile; return $false }
    try {
        Log-HermesQb "  Plex refresh section $script:HermesQbPlexShowsSection..." $LogFile
        $r = Invoke-WebRequest -UseBasicParsing -Uri "$script:HermesQbPlexBase/library/sections/$script:HermesQbPlexShowsSection/refresh" -Method Get -TimeoutSec 30 -Headers @{"X-Plex-Token"=$token}
        Log-HermesQb "  Plex: HTTP $($r.StatusCode)" $LogFile
        return $true
    } catch {
        Log-HermesQb "  Plex FAILED: $($_.Exception.Message)" $LogFile
        return $false
    }
}
