# YOU (2018) — Bad Flatten Cleanup + Gap Fill Pattern

Session lesson: a show can look like it has a season folder while actually containing the wrong episode codes. Do not trust folder names alone.

## Failure shape observed

`D:\Shows\You (2018)` appeared to have Season 1/3/4/5, but inspection showed:

- `Season 1 (2018)` contained misplaced `S03E10` and duplicate `S04E01-S04E10`, not actual Season 1.
- `Season 5 (2025)` contained duplicate copies and zero-byte placeholders.
- qBittorrent initially had no relevant active torrents, so this was stale local library state rather than an active incomplete transfer.

## Correct sequence

1. Audit actual episode codes recursively before deciding what is present.
   - Count `S##E##` codes.
   - Detect duplicate codes.
   - Detect zero-byte media placeholders.
   - Detect episode codes under the wrong season folder.
2. Move wrong-but-valid files into the correct canonical season folder when there is no target collision.
3. Move duplicate losers and zero-byte placeholders out of Plex into a dated cleanup folder with a manifest.
   - Prefer quarantine under `D:\HermesCleanup\YYYY-MM-DD\<show>-fix\`.
   - Do not hard-delete unless Xan explicitly asks.
4. Run show gap analysis after cleanup, not before, because bogus season folders distort what is missing.
5. For short/common show names such as `You`, search with year and exact episode title when possible.
6. Strictly validate search results by title boundary and episode/title. Reject wrong-title bait even when it has high seed count.
   - Example false positive: `Have I Got News For You S03E04` matched a naive `You S03E04` query but is the wrong show.
7. Add missing bundles/episodes with `--type show` and destination `D:\Shows\Show Title (Year)`.
8. While downloads are active, do not treat root-level files or torrent wrapper folders as final layout. Final audit happens after completion/flattening.
9. If the batch watcher is waiting on stalled/dead torrents, search replacements for those exact episode codes rather than waiting indefinitely.

## Verification gates

- No duplicate `S##E##` codes.
- No zero-byte video files.
- No episode codes stored under the wrong season folder.
- No non-season wrapper folders after downloads finish and flattening runs.
- Malware scan passes.
- Plex Shows refresh triggered after cleanup and again after final completion.

## Search/pick notes from this case

- `You 2018 S01 1080p` found a usable S01 bundle.
- `You 2018 S02 1080p` found a healthy S02 bundle.
- `You S03E04 Hands Across Madre Linda` was safer than `You.S03E04` because the latter surfaced wrong-show bait.
- Prefer exact `You.S03E##.<episode-title>` results for S03 gap fills when bundles are not available.