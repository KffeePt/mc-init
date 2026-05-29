# qbittorrent-on-added.ps1
# qBittorrent: Run external program on torrent added
# Smart registry role: add/update active show downloads with telemetry/ranking.

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
$mediaType = Get-HermesMediaType $Category $SavePath $ContentPath
if ($mediaType -ne "show") {
    Log-HermesQb "IGNORED_NON_SHOW | media_type=$mediaType | category=$Category | hash=$InfoHash | $TorrentName | save=$SavePath | content=$ContentPath" $script:HermesQbAddedLog
    exit 0
}

$key = Get-HermesRegistryKey $TorrentName $SavePath $InfoHash
$mutex = New-Object System.Threading.Mutex($false, $script:HermesQbMutexName)
$hasLock = $false
try {
    $hasLock = $mutex.WaitOne([TimeSpan]::FromSeconds(30))
    if (-not $hasLock) { throw "Timed out waiting for registry lock" }

    $reg = Read-HermesRegistry $script:HermesQbAddedLog
    if (-not $reg.items.Contains($key)) {
        $reg.items[$key] = New-HermesRegistryItem $TorrentName $ContentPath $SavePath $InfoHash $Category "active"
        Log-HermesQb "ADDED | key=$key | hash=$InfoHash | $TorrentName | save=$SavePath | content=$ContentPath" $script:HermesQbAddedLog
    } else {
        $item = $reg.items[$key]
        $item.name = $TorrentName
        $item.content_path = $ContentPath
        $item.save_path = $SavePath
        $item.info_hash = $InfoHash
        $item.category = $Category
        $item.media_type = $mediaType
        $item.show_root = Resolve-HermesShowRoot $item
        if ($item.status -ne "flattened") { $item.status = "active" }
        Log-HermesQb "ADDED_UPDATE | key=$key | hash=$InfoHash | $TorrentName | save=$SavePath | content=$ContentPath" $script:HermesQbAddedLog
    }

    $torrents = Get-HermesQbTorrents $script:HermesQbAddedLog
    $reg = Update-HermesRegistryTelemetry $reg $torrents $script:HermesQbAddedLog
    $reg.decision = [ordered]@{ event="added"; key=$key; at=(Get-Date -Format "o") }
    Write-HermesRegistry $reg
} catch {
    Log-HermesQb "REGISTRY_WRITE_FAILED: $($_.Exception.Message)" $script:HermesQbAddedLog
} finally {
    if ($hasLock) { $mutex.ReleaseMutex() | Out-Null }
    $mutex.Dispose()
}
