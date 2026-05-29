# Smart flattener collision verification

Use this when a show download batch reports complete and Xan asks whether the smart flattener worked, especially when there was an explicit collision policy such as “keep the newly downloaded media over the old one.”

## Durable lesson

Do not treat qBittorrent completion, an empty torrent list, or a watcher success line as proof that the media library is correct. The real verification target is the Plex-visible filesystem state plus the collision manifest/review state.

## Verification sequence

1. Check qBittorrent only as queue state:
   - confirm the relevant torrents are no longer active, or that any remaining torrents are unrelated;
   - if removing completed torrents from the list, use qBittorrent’s keep-files mode (`deleteFiles=false`).
2. Inspect the show root under `D:\Shows\<Show Title (Year)>`:
   - no torrent wrapper directories should remain;
   - no root-level episode files should remain;
   - episodes should live in canonical `Season N (Year)` folders.
3. Audit episode-code duplicates:
   - group files by `S##E##` recursively;
   - duplicate groups are not automatically bad until compared against the collision policy, but they block a clean success report.
4. Inspect collision/review markers:
   - look for `__COLLISION_REVIEW`, `old -`, `new -`, review sidecars, and `D:\Review\current\review.yaml`;
   - if a manifest exists, verify which file was promoted into Plex and which was moved aside.
5. Apply the explicit policy:
   - if Xan says to keep newly downloaded media, prefer the new/remote file using collision metadata first, then mtime/release folder/expected quality as secondary evidence;
   - move the loser outside Plex into `D:\HermesCleanup\<date>\...` or the configured review/archive location with a small manifest;
   - do not hard-delete unless Xan explicitly asks.
6. Re-audit after cleanup:
   - duplicate episode-code groups should be zero for the in-scope season/episodes;
   - collision markers should be gone from the Plex-visible show tree;
   - the kept/new file should still exist under the canonical season folder.
7. Refresh Plex only after the filesystem state is clean.

## Reporting pattern

Report observed facts separately from inference:

- Queue: active/empty, removed from qBittorrent with keep-files if applicable.
- Filesystem: canonical season folders present, wrappers/root files absent/present.
- Collision: policy applied, kept new media, moved old media to review/cleanup path.
- Remaining risk: any specials, unmatched extras, ambiguous duplicates, or Plex section uncertainty.

## Pitfalls

- “Everything downloaded” is only a transfer claim. It says nothing about folder shape or collision resolution.
- Smart flattener success can still leave stale old files, alternate season folders, or review markers behind.
- Specials without `S##E##` codes are not normal episode collisions; preserve them unless the user explicitly scopes them in.
- qBittorrent list cleanup is not filesystem cleanup. Removing torrents with keep-files only affects the client state.
