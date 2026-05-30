# qBittorrent Event Hooks — Show Download Automation

Session learning: keep qBittorrent automation scripts under the shared Hermes workspace, not ad-hoc drive script roots, so every local agent can inspect, update, and hand off cleanly.

## Canonical script location

Windows path:

```text
C:\Users\santi\Documents\Hermes\Scripts\
```

WSL path:

```text
/mnt/c/Users/santi/Documents/Hermes/Scripts/
```

Production scripts:

- `qbittorrent-on-added.ps1`
- `qbittorrent-on-finished.ps1`

Do not deploy future qBittorrent/Plex show automation under `D:\Scripts\` unless Xan explicitly asks. The shared Hermes workspace is the durable operational location.

## qBittorrent GUI commands

Set these in qBittorrent GUI → Tools → Options → Downloads.

Run external program on torrent added:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\santi\Documents\Hermes\Scripts\qbittorrent-on-added.ps1" "%F" "%N" "%L" "%D"
```

Run external program on torrent completion:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\santi\Documents\Hermes\Scripts\qbittorrent-on-finished.ps1" "%F" "%N" "%L" "%D"
```

## State files and logs

The scripts should keep their operational state beside the scripts unless intentionally configured otherwise:

- `qbittorrent-active.json` — active torrent state for agent awareness without polling qBittorrent API or running token-wasting cron jobs
- `qbittorrent-on-added.log` — addition hook log
- `qbittorrent-on-finished.log` — completion/flatten/Plex refresh log

If migrating from an older location, copy scripts, logs, and active JSON state together, then update qBittorrent GUI hook commands. Do not leave qBittorrent pointing to stale paths.

## Behavior contract

- On added: log torrent name/path/category, update `qbittorrent-active.json`.
- On finished: **flatten the completed item immediately**. Active batch siblings must not block filesystem organization. This avoids the YOU failure mode where one completed season stayed in a wrapper because unrelated gap-fill torrents were still active/stalled.
- Plex refresh is debounced, not immediate-per-file: completion events whose metadata timestamps fall inside the same 5-minute window share one delayed Plex library refresh. Events outside that window create a new refresh window. This prevents Plex API bombardment when many torrents finish together while still keeping flattening per-success.
- Root resolution should prefer canonical `D:\Shows\Title (Year)` folders using title/year fuzzy matching before treating release-wrapper names like `Title (Year) Season 01 ...` as show roots. For short ambiguous titles like `YOU`, require year/title evidence where possible.
- Use `Copy-Item -LiteralPath` for qBittorrent-seeded files when files are still locked; direct `Move-Item` is acceptable only after the hook removes the completed torrent with `deleteFiles=false`.
- Parse-verify PowerShell scripts with `[System.Management.Automation.Language.Parser]::ParseFile()` after edits.

## Verification after relocation

1. Confirm both scripts exist in the Hermes Scripts directory.
2. Confirm qBittorrent GUI hook commands reference the Hermes Scripts directory, not `D:\Scripts`.
3. Manually run the added hook against a known torrent name/path and verify `qbittorrent-active.json` updates.
4. When a torrent completes, verify the finished hook logs, state cleanup, flat season folders, and Plex refresh.
