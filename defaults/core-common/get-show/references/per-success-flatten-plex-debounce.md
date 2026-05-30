# Per-success flattening + 5-minute Plex refresh debounce

Session learning from the YOU (2018) S1 wrapper failure and subsequent qBittorrent hook patch.

## Durable rule

Completed downloads must be organized immediately. Batch state must never block filesystem flattening just because sibling torrents are still active, stalled, metadata-only, or near-finished.

Batching is only for expensive downstream side effects — especially Plex library refreshes.

## Correct behavior

1. qBittorrent completion hook fires for one completed torrent.
2. Identify media type from category/path.
3. Resolve the canonical library root.
   - Prefer `D:\Shows\Title (Year)` or `D:\Movies\Title (Year)`.
   - For short/ambiguous show titles, use title/year evidence before trusting the first path segment.
   - Release wrappers like `YOU (2018) Season 01 ...` are not canonical roots.
4. Remove the completed torrent from qBittorrent with `deleteFiles=false` before moving files.
5. Flatten the completed root immediately.
6. Record a pending Plex refresh event.
7. Debounce Plex refreshes into a 300-second window from the first pending event.
   - Completions inside that window share one delayed Plex refresh.
   - Completions after that window create a new refresh window.

## Why this matters

The previous batch barrier waited on unrelated active/stalled torrents before flattening completed items. In the YOU case, S1 finished and seeded, but the release wrapper remained under the show root because other S3 gap-fill torrents were still stuck in `metaDL`. Plex could refresh while the disk layout was still wrong. That is exactly backwards.

Correct separation:

- Flattening: per-success, immediate, local filesystem correctness.
- Plex refresh: debounced, delayed, API-noise reduction.

## Verification pattern

After patching or troubleshooting this class of hook:

1. Parse-verify PowerShell scripts:
   - `qbittorrent-batch-lib.ps1`
   - `qbittorrent-on-finished.ps1`
   - debounce worker script if present
2. Test wrapper-root resolution with a short-title release path, e.g. `YOU (2018) Season 01 ...` must resolve to `D:\Shows\You (2018)`.
3. Test debounce state in isolation:
   - two refresh requests inside the window should produce one pending state with `event_count=2`
   - due time should be first event + 300 seconds
4. Re-audit the target media root:
   - no root-level episode files
   - no release wrapper folders
   - no duplicate episode codes
   - no collision/review markers unless intentionally queued
5. Confirm qBittorrent completion hook is enabled and points at the shared Hermes script path with the info-hash argument.

## Last-resort fallback

If canonical root resolution still fails after fuzzy title/year matching, only then use a localized Hermes CLI or IMDb-assisted move-command generator. Keep that fallback scoped to one media root, generate explicit move commands, and execute them through normal tools with verification. Do not let broad IMDb search drive library-wide moves blindly.
