# 2026-05-28 — Movie smart flatten and review queue architecture

## Context

The show smart flattener already staged hash-different collisions under `D:\Review`. Xan requested equivalent movie-specific logic and wanted newly downloaded media to win by default when a collision exists.

## Architecture

Movie completion flow should use the same shared qBittorrent hook library as shows:

- `C:\Users\santi\Documents\Hermes\Scripts\qbittorrent-batch-lib.ps1`
- `C:\Users\santi\Documents\Hermes\Scripts\qbittorrent-on-finished.ps1`
- `C:\Users\santi\Documents\Hermes\Scripts\wilson-smart-org.ps1`

Movie-specific logic:

1. Resolve root from qBittorrent content/save path, but refuse to operate on bare `D:\Movies`.
2. Flatten nested torrent wrapper folders so media files live directly under `D:\Movies\Movie Title (Year)\`.
3. Move/copy subtitle and metadata sidecars that match movie base names.
4. If target exists and source/target hashes match, remove the duplicate wrapper copy.
5. If target exists and hashes differ, default to `remote/new`:
   - queue old/local under `D:\Review\YYYY-MM-DD\HH-MM-SS\`
   - expose current review files under `D:\Review\current\`
   - update `D:\Review\current\review.yaml`
   - move the new movie into the Plex library target path
6. Refresh Plex Movies section after movie moves/collisions.
7. Use `smart_org.bat` / `WILSON_Hash_Verify.bat` as manual entry points. The legacy hash-verify launcher is a wrapper for the full organizer now.

## Locked-file pitfall

Windows, qBittorrent, Plex, or antivirus may briefly hold read handles on a completed movie. For flattening, prefer:

1. `Move-Item`
2. fallback to `Copy-Item`
3. try source cleanup
4. if source cleanup is still locked, log a deferred cleanup message and let a later pass remove it

Do not report a failed move as a completed flatten unless the copy fallback actually placed the library file.

## Review decision semantics

- `remote` or Enter: keep newly downloaded media [default]
- `local`: restore old/local media over the new file
- `merge`: keep both in library with `new - ` and `old - ` prefixes
- `skip`: leave item open

## Verification fixture

Use a disposable movie root named like `D:\Movies\__WilsonMovieReviewTest (2026)` with an old file in the root and a different new file in a wrapper folder. Expected outcome:

- collision count at least 1
- root file content/hash equals new/remote
- review YAML contains an open movie collision item
- cleanup removes fixture and test review entries afterward