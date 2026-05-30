# qBittorrent Adaptive Flatten Batching

Session lesson: a strict "wait until every active show torrent finishes" batch barrier is too blunt. It prevents premature flattening, but one slow long-tail torrent can hold completed downloads hostage and leave Plex stale.

## Better class-level pattern

Use the torrent-added and torrent-finished hooks as event triggers, but make the registry scheduler smarter:

1. On torrent add, record each show torrent in a JSON hashmap keyed by info hash.
2. Store live/schedulable metadata, not just `active`:
   - `size_bytes`
   - `completed_bytes`
   - `remaining_bytes`
   - `progress`
   - `download_speed_bps`
   - qBittorrent `eta`
   - computed ETA from remaining bytes / speed
   - seeds, peers, availability when available
   - reliability score
   - rank and ETA group
3. On torrent finish, refresh qBittorrent telemetry for every registry item before deciding.
4. Flush completed groups when waiting is mathematically not worth it.
5. Keep slow/incomplete torrents active in the registry, but do not let them block completed roots.

## Suggested ETA groups

- `ready_now`: complete
- `near`: ETA under ~10 minutes and reliability is acceptable
- `medium`: ETA under ~45 minutes
- `long_tail`: ETA over ~45 minutes
- `stalled`: no speed and weak seeds/availability

## Wait-vs-flush decision

Flush completed show roots now when:

- at least one completed root exists, and
- any remaining active torrent is medium/long-tail/stalled, or
- completed content exceeds a useful batch size threshold, or
- enough time has elapsed since the last Plex scan.

Wait when:

- every active item is near-finished, and
- max ETA is within the short wait threshold, and
- reliability is acceptable.

## Critical safety rule

Sort/rank torrent jobs by size/ETA/reliability for scheduling only. Do **not** sort or arrange media files by size. Final library layout remains Plex-friendly:

```text
D:\Shows\Show Title (Year)\Season N (Year)\episode files
```

Never flatten active/incomplete content paths. Completed roots may be flushed independently; incomplete roots must stay untouched.

## Logging requirements

Logs should explain scheduler decisions:

- `FLUSH`: completed candidates, blockers, reason
- `WAIT`: near-finished blockers with ETA/reliability
- `SKIP_ACTIVE`: active content path excluded
- `REGISTRY_RECONCILE`: live qBittorrent status differed from stored registry state

## Verification recipe

Before trusting production:

1. Simulate registry states for: near wait, long-tail flush, stalled flush, all complete, and active incomplete exclusion.
2. Parser-check PowerShell hooks.
3. Run against current qBittorrent state and verify the intended decision before moving files.
4. After flattening, audit each show root for:
   - zero root-level episode files
   - zero non-season wrapper video episode files
   - expected `Season N (Year)` folders
5. Trigger Plex Shows refresh only after actual file movement.
