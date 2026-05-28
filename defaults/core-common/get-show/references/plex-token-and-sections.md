# Plex API Token & Section Mapping — Xan's Server

Last verified: 2026-05-27

## Token Retrieval

The Plex token is stored in the Windows registry:

```powershell
Get-ItemProperty -Path "HKCU:\Software\Plex, Inc.\Plex Media Server" | Select-Object PlexOnlineToken
```

Alternatively, find it in:
- `%LOCALAPPDATA%\Plex Media Server\Preferences.xml` → `PlexOnlineToken` attribute

## Section Mapping (post-consolidation)

MAMBA (`F:\Shows`) and the old `More Shows` library have been consolidated into a single `D:\Shows` library. Verify the current section ID via token retrieval before refreshing.

| Section ID | Name | Path | Status |
|---|---|---|---|
| 1 | Movies | `D:\Movies\` | Active |
| 5 | Música | `D:\Music\` | Active |
| — | Shows (consolidated) | `D:\Shows\` | Active — section ID may have changed post-consolidation; verify via Plex API |
| 2 | Shows (legacy) | `F:\Shows\` | ⛔ Deprecated |
| 6 | More Shows (legacy) | `D:\Shows\` | ⛔ Deprecated |

## Refresh API

Retrieve the current section ID first:
```
GET http://localhost:32400/library/sections
Header: X-Plex-Token: <token>
```

Then refresh the correct section:
```
GET http://localhost:32400/library/sections/<id>/refresh
Header: X-Plex-Token: <token>
```

Response: HTTP 200 (refresh queued). Plex handles duplicate/overlapping refresh requests gracefully.

## qBittorrent Completion Hook

The deployed scripts are at `C:\Users\santi\Documents\Hermes\Scripts\`:
- `qbittorrent-on-added.ps1` — logs additions
- `qbittorrent-on-finished.ps1` — flattens + refreshes Plex

The on-finished script's Plex section target may need updating post-consolidation. Verify it points to the current consolidated D:\Shows section ID.

## Pitfalls

- **Don't use `Move-Item` on qBittorrent files.** During active download, files have exclusive write locks. During seeding, read locks block Move-Item. Use `Copy-Item` then conditional `Remove-Item` with catch.
- **Don't use `robocopy /MOV` from WSL-launched PowerShell.** Path quoting through the WSL→PowerShell→robocopy chain breaks on spaces. `Copy-Item -LiteralPath` is safer.
- **PowerShell heredoc backslash doubling.** `@"..."@` here-strings preserve backslashes literally, but when the string is written from WSL, double-check regex patterns like `'^D:\\Shows'` haven't been mangled.
- **Plex token changes on Plex account re-auth.** If Plex refresh starts returning 401, re-retrieve the token from the registry.
