# 2026-05-27 — qBittorrent Batch Registry + Show Flatten Hooks

## Trigger

Use this reference when working on qBittorrent torrent-added / torrent-finished hooks that organize TV downloads into `D:\Shows` show roots and season folders.

## Durable pattern

For concurrent torrent additions, do **not** let each `torrent finished` hook flatten immediately. qBittorrent can fire multiple hook processes close together, and per-item flattening races against downloads from the same batch.

Preferred design:

1. Agent-added torrents must carry an explicit qBittorrent category/media type (`movie`, `tv`, or `music`); do not infer from title strings when the agent can set a flag.
2. `OnTorrentAdded` derives `media_type` from category first, then save/content root as fallback.
3. Only `media_type=show` entries are written to the Shows batch registry; movie/music/unknown entries are logged and ignored by the show flattener.
4. Registry shape is a hashmap keyed by a stable torrent identifier.
5. All registry writes are guarded by a Windows global mutex.
6. `OnTorrentFinished` marks show items `finished`.
7. If any registry item remains `active`, log `DEFER` and exit.
8. When no active items remain, snapshot completed items, clear the registry, then flatten every completed `D:\Shows` root once.
9. Refresh Plex only after the batch flatten pass.

## Registry shape

Use an object/hashmap, not a fragile PowerShell array JSON shape:

```json
{
  "schema_version": 2,
  "batch_started_at": "2026-05-27T16:19:47-06:00",
  "updated_at": "2026-05-27T16:19:47-06:00",
  "items": {
    "short_key": {
      "name": "Torrent Name",
      "content_path": "D:\\Shows\\Show Root",
      "save_path": "D:\\\\Shows",
      "info_hash": "<qBittorrent %I if available>",
      "category": "tv",
      "media_type": "show",
      "added_at": "...",

      "status": "active"
    }
  }
}
```

Best key: qBittorrent info hash if the hook command passes it. If the current command does not pass info hash, use a digest of torrent name + save path, but note the collision risk for duplicate names.

## Hook command shape

Paste-ready hardened command shape using qBittorrent `%I` as the info-hash:

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\santi\Documents\Hermes\Scripts\qbittorrent-on-added.ps1" "%F" "%N" "%L" "%D" "%I"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\santi\Documents\Hermes\Scripts\qbittorrent-on-finished.ps1" "%F" "%N" "%L" "%D" "%I"
```

Scripts should accept the fifth optional parameter as `InfoHash`, use it as the registry key when non-empty, and fall back to a digest of torrent name + save path for manual tests or older qBittorrent builds that pass literal `%I`.

## Safety requirements

- Prefer explicit qBittorrent category over filename inference. `movie`/`movies` routes to Movies, `tv`/`show`/`series` routes to Shows, `music` routes to Music. If category is absent, fall back to path-root checks (`D:\\Shows`, `D:\\Movies`, `D:\\Music`). If still unknown, skip automation and log for review.
- Hard-refuse to flatten `D:\Shows` itself.
- Use `Move-Item` for same-volume flattening instead of copy/delete where possible.
- Remove empty nested directories after moves, but keep the show root and season directories.
- Do not overwrite collisions blindly. Never use `Move-Item -Force` for flattened episode moves. If destination exists and size matches, compare SHA-256 hashes; remove the duplicate source only when hashes match. If content differs, preserve the incoming file with a `__COLLISION_REVIEW_<timestamp>_<hash>` suffix in the target season folder and log/count it for review.

## Watcher-vs-hook pitfall

Do not confuse qBittorrent batch watchers with the flatten hooks. A watcher may report completion, scan files, and refresh Plex while episode files still sit at the show root or inside torrent wrapper folders. The durable success condition is filesystem shape, not watcher completion:

- no root-level episode files under `D:\Shows\<Show Title (Year)>`
- no release-name wrapper directories such as `www.UIndex.org...` or full torrent pack names
- episodes grouped under canonical `Season N (Year)` folders

If watcher completion and filesystem shape disagree, the flattener did not run or did not process that torrent. Patch the post-completion path or run a manual flatten pass, then re-audit the folder before claiming success.

Current hardened shape: `watch_batch.py` is also a flatten fallback for show batches. After all torrents in a watched show batch complete, it resolves qBittorrent `save_path` / `content_path` to `D:\Shows\<Show Title (Year)>`, flattens into canonical `Season N (Year)` folders, then refreshes Plex. Existing watcher processes must be restarted after patching the script because long-running Python processes keep the old code loaded.

## Manual catch-up flattening while downloads are active

When hooks defer because a registry still contains active items, a manual catch-up pass may be useful for torrents that are already complete. Do not just sweep `D:\Shows` recursively. First query qBittorrent's structured API (`/api/v2/torrents/info` or equivalent client wrapper) and build an exclusion set from incomplete torrents' `content_path`, `save_path`, and names. Then flatten only show roots not associated with active/incomplete torrents.

Operational checks:

- Skip any source path containing `.part` files or matching an incomplete torrent content/save path.
- Keep routing type-aware: only flatten `media_type=show`, `category=tv/show/series`, or paths rooted under `D:\Shows`; never apply show flattening to Movies.
- For completed show torrents, move episode files into canonical `Season N (Year)` folders, remove empty wrapper directories, and verify no root-level episode files remain.
- Report skipped active paths explicitly so the user understands why some shows are still unflattened.
- Trigger Plex Shows refresh after show flattening; trigger Movies refresh only for completed movie acquisitions, not as a side effect of show cleanup.

## Name cleanup pitfall

Do not use an overbroad URL regex that removes any dotted token. It will destroy normal release-style names like `Test.Show.S01E01.mkv`.

Safer cleanup targets:

- `https?://...`
- `www.<domain>.<tld>`
- known tracker domains like `eztv`, `rarbg`, `uindex`, `torrentgalaxy`, `tgx`
- bracketed tracker/release tags like `[EZTVx.to]`

Verify at least these cases:

```text
www.UIndex.org - Test.Show.S01E01.mkv -> Test.Show.S01E01.mkv
[EZTVx.to] Test.Show.S01E01.en.srt -> Test.Show.S01E01.en.srt
Test.Show.S01E01.mkv -> Test.Show.S01E01.mkv
```

## Verification recipe

Minimum verification after editing hooks:

1. PowerShell parser check both scripts.
2. Simulate two `added` events into different temporary `D:\Shows\__HermesHookTest*` roots.
3. Finish the first item and verify log shows defer behavior and registry still contains the second active item.
4. Finish the second item and verify registry clears.
5. Create a temporary nested show root with URL/bracket junk names.
6. Run the finished hook and verify files land under `Season 1 (Year)` / `Season 2 (Year)` folders with cleaned names.
7. Verify temp nested directories are removed.
8. Query Plex sections before hardcoding a refresh section; section IDs drift.
9. Remove temporary test roots.

## Plex note from this host

On 2026-05-27 this host returned these live Plex sections:

```text
1 = Movies
2 = Shows
5 = Música
4 = Edits
```

Section `6` returned 404 and was stale. Query live sections instead of trusting old notes.
