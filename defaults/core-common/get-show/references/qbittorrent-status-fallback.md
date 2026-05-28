# qBittorrent Status Fallback from WSL

## When this applies

Use this when a show torrent was selected/added and follow-up verification is needed, especially if:

- `media_search.py status --filter "..."` fails with JSON parse errors.
- WSL `curl http://localhost:8080/api/v2/...` cannot connect.
- The Windows-host qBittorrent Web UI is expected to be running on port 8080.

This is a host-context issue, not proof that qBittorrent is down.

## Pattern

Query qBittorrent from Windows PowerShell so `localhost` means the Windows host:

```powershell
$ProgressPreference="SilentlyContinue"
$base="http://localhost:8080/api/v2"
$s=New-Object Microsoft.PowerShell.Commands.WebRequestSession
Invoke-WebRequest -UseBasicParsing -Uri "$base/auth/login" -Method Post -Body @{username=$env:QBITTORRENT_USERNAME;password=$env:QBITTORRENT_PASSWORD} -WebSession $s
$json=(Invoke-WebRequest -UseBasicParsing -Uri "$base/torrents/info?filter=all" -WebSession $s).Content
$json | ConvertFrom-Json |
  Where-Object { $_.name -match "Billy|Mandy|Grim" } |
  Select-Object name,hash,state,progress,dlspeed,upspeed,num_seeds,num_leechs,size,save_path,completion_on
```

From WSL, run it through `powershell.exe -NoProfile -Command '...'`. Wrap the whole script in single quotes so WSL does not expand PowerShell `$` variables.

## Interpretation

If the selected torrent is already present and `save_path` is `D:\Shows\<ShowName>`:

- Do not re-add the torrent.
- Report state/progress/speed/seeds/save path.
- Remaining work is completion, malware scan, and optional Plex verification.

If the torrent is present but points at `F:\Shows` or another legacy path:

- Use qBittorrent `torrents/setLocation` deliberately.
- Poll until state is no longer `moving`.
- Verify `save_path` after the move, not just the initial API response.

## Pitfall

Do not let a failed WSL-side status command trigger a redundant search/add cycle. Check the Windows-side Web UI first. Duplicate torrents are operational mold.