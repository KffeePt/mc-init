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
- On finished: remove torrent from active state, flatten show-pack folders into `S1/`, `S2/`, etc., move sidecars with episodes, remove empty wrappers, refresh Plex section 6 (`More Shows` → `D:\Shows`).
- Use `Copy-Item -LiteralPath` for qBittorrent-seeded files, not `Move-Item`.
- Parse-verify PowerShell scripts with `[System.Management.Automation.Language.Parser]::ParseFile()` after edits.

## Verification after relocation

1. Confirm both scripts exist in the Hermes Scripts directory.
2. Confirm qBittorrent GUI hook commands reference the Hermes Scripts directory, not `D:\Scripts`.
3. Manually run the added hook against a known torrent name/path and verify `qbittorrent-active.json` updates.
4. When a torrent completes, verify the finished hook logs, state cleanup, flat season folders, and Plex refresh.
