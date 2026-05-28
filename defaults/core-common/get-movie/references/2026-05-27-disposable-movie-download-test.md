# 2026-05-27 — Disposable Movie Download Test Pattern

## Trigger

Use this when Xan asks to test qBittorrent/movie automation with a low-quality throwaway download and delete it afterward.

## Objective

Verify the end-to-end path without leaving permanent media:

1. Add a small, safe movie torrent to qBittorrent.
2. Download into the final intended folder shape, e.g. `D:\Movies\Alien Romulus (2024)\`.
3. Confirm a media file appears and reaches 100%.
4. Delete the torrent with `deleteFiles=true`.
5. Remove the empty test folder.
6. Verify no matching torrent remains and no test folder remains.

## Candidate selection

- Prefer **720p** over random 480p when 480p options are unsafe, dubbed, malware-looking, or dead.
- Avoid `.exe`, `.scr`, `.iso`, double-extension media bait, cam/HDTS unless the user explicitly wants that trash-fire.
- A slightly larger healthy 720p test is better than a tiny dead 480p torrent.
- If an initial test candidate stalls, remove it and retry with a healthier swarm. Capture the retry pattern, not the transient failure.

## qBittorrent cleanup pattern

Use the Windows-side qBittorrent API from WSL via PowerShell when needed:

```powershell
$base = "http://localhost:8080/api/v2"
$s = New-Object Microsoft.PowerShell.Commands.WebRequestSession
Invoke-WebRequest -UseBasicParsing -Uri "$base/auth/login" -Method Post -Body @{username=$env:QBITTORRENT_USERNAME;password=$env:QBITTORRENT_PASSWORD} -WebSession $s | Out-Null
$t = (Invoke-WebRequest -UseBasicParsing -Uri "$base/torrents/info?filter=all" -WebSession $s).Content |
  ConvertFrom-Json |
  Where-Object { $_.name -match "Alien.*Romulus" }
if ($t) {
  $hashes = ($t.hash -join "|")
  Invoke-WebRequest -UseBasicParsing -Uri "$base/torrents/delete" -Method Post -Body @{hashes=$hashes; deleteFiles="true"} -WebSession $s | Out-Null
}
```

## Verification checklist

- `qBittorrent` shows 0 matching torrents after cleanup.
- Test movie folder is gone or empty and removed.
- If using a watcher, kill stale watcher before deleting/replacing the torrent.
- If testing folder-normalization simultaneously, download into `D:\Movies\Title (Year)\`, not the library root.

## Reporting

Report:

- candidate selected and why
- destination path
- completion status
- cleanup status
- whether any artifacts/logs were produced
- remaining work, if any
