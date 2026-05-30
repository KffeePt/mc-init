# Stalled Source Replacement — Dead Little Things

Problem: qBittorrent can keep episode torrents alive but useless in `metaDL`, `stalledDL`, waiting-for-peers, `0%`, zero-size, or zero-seed states. They look active enough to clutter operations but never produce media.

## Activation Policy — Manual / Opportunistic Only

This workflow is **not** a scheduled watchdog and must not be run as a background/cron-style automatic sweep.

Run stalled-source detection only when one of these is true:

1. Xan explicitly asks for dead/stalled source detection, stalled torrent cleanup, or replacement planning.
2. While doing another requested media task, you already inspect qBittorrent/download status and notice stalled/dead episode torrents as part of that task.

Do **not** proactively poll qBittorrent just to hunt stalled sources. Do **not** create cron jobs or background loops for this. Detection is operator-requested or opportunistic, not ambient surveillance. The dead can wait. They usually do.

## Detection

Use only under the activation policy above:

```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py stalled --filter "Show Name" --limit 5
python3 /home/xantastique/.hermes/skills/media/media_search.py stalled --filter "Show Name" --json
```

A torrent is treated as a dead/stalled episode candidate when it has an `S##E##` token and is incomplete with no useful swarm evidence, especially:

- progress under ~0.1% and no download speed
- zero seeds
- zero size / metadata-only
- qBittorrent status like waiting-for-peers or metadata download

## Replacement policy

1. Extract show title from canonical `save_path` first. Torrent names are polluted; short titles like `YOU` are especially dangerous.
2. Extract exact episode code `S##E##` from the stalled torrent.
3. Search public indexers using title/year/code and episode-title context.
4. Reject wrong-series matches even if they contain the same episode code.
5. Rank replacements by:
   - 1080p sweet spot first
   - WEB-DL/BluRay/REMUX over HDTV/unknown/low-grade sources
   - x265/HEVC preferred when otherwise comparable
   - healthy swarm / seed count
   - sane size
   - known/trusted group
6. Default behavior is detection/reporting only. Do not auto-add replacements just because a stalled source exists.
7. `--auto-add-obvious` is allowed only when Xan explicitly asks to replace/add obvious stalled-source replacements, or when he has already delegated the surrounding media task and the candidate is a single clear winner:

```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py stalled --filter "Show Name" --auto-add-obvious
```

If the top candidate has weak seeds, the candidates are close, title validation is ambiguous, no exact match exists, or the current task was only status/reporting, present choices to Xan. Do not guess. Wrong-title bait is worse than waiting.

## Current YOU lesson

For `You (2018)` S3 gap-fill torrents, the stalled planner detected 8 dead sources and rejected unrelated `Charmed (2018)` false positives that matched only `S03E04/S03E05` plus episode-title words. This is correct behavior: no public replacement is better than a confidently wrong replacement.
