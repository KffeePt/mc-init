# qBittorrent watchers vs flatten hooks

Use this when checking whether a show download batch finished *and* landed in Xan's required flat season-folder structure.

## Lesson

`watch_batch.py` and the qBittorrent PowerShell completion hooks are different systems:

- `watch_batch.py` waits for qBittorrent completion, runs a light scan, and refreshes Plex.
- The PowerShell `qbittorrent-on-finished.ps1` hook is the component intended to flatten nested torrent folders into `Season N (Year)` folders.

Do not assume watcher completion means flattening happened.

## Required verification after show downloads complete

For each completed show batch, inspect the actual folder shape under `D:\Shows\<Show Title (Year)>\`:

- Root-level episode files are not acceptable unless the show intentionally has no season folder.
- Torrent wrapper directories such as release names, `www.UIndex.org`, or full pack names are not acceptable final structure.
- Expected final shape is direct season folders, e.g. `Season 4 (2025)` containing `S04E##` files.

## Red flags

- Watcher says complete, but show folder still contains release-wrapper directories.
- qBittorrent active registry is empty, but the hook log has no entries for the real torrent names.
- Plex refresh happened but folder hygiene is still wrong.
- Episodes appear in Plex while files remain at the show root or under wrappers.

## Fix path

1. Patch the watcher or post-completion flow so show batches explicitly run the same flatten/organize logic after all torrents in that show batch are complete.
2. Until that is fixed, run a manual flatten/organize pass for completed shows before claiming the pipeline succeeded.
3. Re-audit folder shape after flattening, not just qBittorrent status.
4. Only then scan and refresh Plex.

## Reporting rule

When Xan asks “did they flatten properly?”, answer based on the filesystem structure, not qBittorrent completion state. If wrappers/root videos remain, say no plainly and name the affected shows.