# Post-Flatten Collision Cleanup — Keep Newly Downloaded Media

Use this when a show download completes and the flattener says it ran, especially after a replacement bundle or a collision-review event.

## Trigger

- qBittorrent reports show downloads complete.
- The completion hook/log says flattening ran.
- Xan says to keep the newly downloaded media over old media.
- `__COLLISION_REVIEW` files or duplicate `SxxEyy` episode codes remain after flattening.

## Procedure

1. Verify qBittorrent state first:
   - Active registry is empty or no relevant show torrents are active.
   - qBittorrent status filter for the show returns no active downloads.

2. Audit the show root, not just the hook log:
   - No root-level episode files.
   - No torrent wrapper directories with episode videos.
   - Count every video file with an `SxxEyy` code.
   - Group by `SxxEyy` and report duplicate groups.
   - Search for `__COLLISION_REVIEW` leftovers.

3. If the policy is “keep newly downloaded media over old media,” rank candidates conservatively:
   - Prefer newest modified time from the just-finished download window.
   - Prefer expected new-release markers/resolution/audio language from the selected torrent.
   - Prefer canonical flattener destination naming when it is clearly the new copy.
   - Demote old release-group files, old dates, and explicit `__COLLISION_REVIEW` suffixes.

4. Move loser files out of the Plex library instead of hard-deleting:
   - Use a cleanup root such as `D:\HermesCleanup\<Show>_<reason>_<date>\`.
   - Preserve relative paths.
   - Write a JSON manifest with source, destination, size, mtime, episode code, and reason.
   - This gives rollback if Plex matching or ordering assumptions were wrong.

5. Clean season-year fragmentation only after deduping:
   - If the newly downloaded pack created alternate year season folders, move remaining non-duplicate new files into the chosen canonical season folder.
   - Remove empty season/wrapper folders afterward.
   - Do not invent semantic correctness; record the chosen convention if air-year folders are collapsed.

6. Preserve no-code Specials unless explicitly asked to remove them:
   - They are not direct `SxxEyy` collisions.
   - Treat them as a separate review if Plex later shows duplicate specials/movie-part entries.

7. Verify again:
   - Duplicate episode groups: `0`.
   - Root-level episode files: `0`.
   - Wrapper episode files: `0`.
   - Collision-review leftovers: `0`.
   - qBittorrent: no active relevant downloads.
   - Malware scan: no critical/high issues.
   - Plex Shows refresh returns HTTP 200.

## Pitfalls

- Watcher completion is not proof of library correctness. The hook can finish while duplicate episode files remain.
- A flattener may copy around locked qBittorrent files and leave source files behind. If the torrent was later removed with files kept, these source remnants can become real Plex duplicates.
- TV ordering for shows like Futurama is messy. Do not delete Specials or alternate-order material just because the season folder looks ugly; remove only direct collision losers unless the user authorizes deeper ordering cleanup.
- Prefer reversible moves over deletion. Permanent deletion is cheap. Undoing a bad Plex-library cleanup is not.