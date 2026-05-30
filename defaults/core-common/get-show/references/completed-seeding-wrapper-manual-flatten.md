# Completed Seeding Wrapper Manual Flatten

## Trigger

Use this when a show torrent is complete in qBittorrent but the show root still contains a torrent-pack wrapper directory instead of canonical `Season N (Year)` folders.

Observed example: `YOU (2018)` Season 1 completed and entered `uploading` at 100%, but the wrapper folder remained under `D:\Shows\You (2018)\`.

## Durable lesson

Do not treat qBittorrent completion, seeding state, or watcher success as proof of final library shape. The authoritative check is the filesystem audit under `D:\Shows\<Show Title (Year)>`.

If a completed torrent is still seeding from the wrapper path, the safest cleanup sequence is:

1. Query qBittorrent from the Windows host API and confirm:
   - `progress == 1`
   - state is complete/seeding/uploading, not downloading/checking/moving
   - `save_path` points at the intended show root
   - `content_path` points at the lingering wrapper
2. Remove the completed torrent with `deleteFiles=false`.
3. Move only media/sidecar files from the wrapper into the canonical season folder.
4. Remove empty wrapper directories after the move.
5. Re-audit before reporting success:
   - no root-level video files
   - no non-season wrapper directories
   - no duplicate `S##E##` groups
   - no collision/review markers
6. Run the show malware scan.
7. Refresh the active Plex Shows section.

## Why this matters

The smart flattener can miss a completed item when hook state, batch barriers, or seeding locks interfere. The failure mode is quiet: Plex refresh may happen while the folder is still ugly. The antidote is boring: inspect the actual folder tree and fix it if necessary. Boring survives contact with Windows.