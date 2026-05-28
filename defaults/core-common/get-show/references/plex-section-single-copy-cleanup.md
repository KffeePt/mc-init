# Plex Section Single-Copy Cleanup Pattern

Use when Xan says a show appears in both Plex `Shows` and `More Shows`, asks to remove the incomplete/legacy copy, or wants exactly one copy visible.

## Key mapping on Xan's server

- Plex `More Shows` maps to `D:\Shows` — active BIGGIE show library.
- Plex `Shows` maps to `F:\Shows` — legacy MAMBA show library.

Do not infer this from Plex section names. Query Plex sections or use the known mapping above.

## Safe workflow

1. Inspect both filesystem roots for the show:
   - `D:\Shows\<Show>`
   - `F:\Shows\<Show>`
2. Count files, media files, and total size for each match.
3. Check qBittorrent for active/completed torrents matching the show and verify `save_path`.
4. If the legacy `F:\Shows` copy is empty, remove only the empty folder.
5. If both roots contain media, do **not** delete by path/name alone. Compare episode codes and exact hashes or prepare a manifest requiring explicit approval.
6. Query Plex API per section after filesystem cleanup:
   - `/library/sections/2/all` for `Shows`
   - `/library/sections/6/all` for `More Shows`
7. Verify target state:
   - zero matching entries in `Shows`
   - exactly one matching entry in `More Shows`
8. Run targeted Plex refreshes only for the relevant sections. Avoid full-library refresh unless explicitly needed.
9. Re-check Plex API health and per-section matches after refresh.

## Pitfalls

- Cartoon/short-segment shows can look incomplete in TVMaze/gap analysis because segment-level episode accounting differs from release/Plex-style episode files. For *The Grim Adventures of Billy & Mandy*, 76 local media files can still trigger many false missing segment reports.
- `--section Shows` must resolve exact `Shows`, not partial `More Shows`. Prefer exact section matching and verify target section ID before refresh.
- If qBittorrent is seeding the D: copy, flattening or moving nested torrent-pack folders can break torrent state. Do not reorganize the tree unless also deliberately handling qBittorrent metadata/location.
- If Plex client UI still shows the deleted legacy entry after Plex API shows zero matches, treat it as client cache/stale UI first.
