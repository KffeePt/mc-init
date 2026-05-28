# 2026-05-27 — Library-Wide TV Gap Audit Pattern

## Trigger

Use this when Xan asks what shows in `D:\Shows` are missing newly aired episodes/seasons or wants an up-to-date library gap sweep rather than a gap check for one named show.

## Pattern

1. Scan active `D:\Shows` show folders only; do not treat archived/deprecated roots as the target library.
2. Parse local episodes from video filenames with multiple patterns: `S##E##`, `#x##`, `Season # Episode #`.
3. Resolve each show against TVMaze using title + year from `Show Title (Year)` folders when available.
4. Compare local episode codes against TVMaze episodes with `airdate <= requested cutoff date`.
5. Split findings into:
   - high-confidence recent/new-season gaps;
   - older backlog gaps;
   - manual-review / unsafe metadata matches.
6. Write both a concise human summary and raw JSON artifacts. The concise summary is what Xan should see first; JSON is for later download planning.

## Manual-review traps

- Anime and long-running shows can use TVMaze season numbering that does not match local/Plex naming. Example: TVMaze may group *One Piece* by year-like seasons while local files use normal season folders. Do not auto-fill from that without manual mapping.
- Anthology/short-segment shows can false-positive when filenames do not map cleanly to TVMaze episode numbers.
- A folder with zero matched local episode codes may be empty, named with nonstandard episode patterns, or matched to the wrong show variant. Treat as review, not as proof the whole show is missing.
- Wrong TVMaze matches are common for generic titles or renamed imports; compare title/year before trusting gaps.

## Output shape

Recommended artifact files:

- `Concise Media Gap Summary.md`
- `show_gap_analysis.json`
- optional full report with all missing episode codes

Recommended chat summary:

- high-confidence recent/new-season gaps first;
- older backlog second;
- manual-review false-positive risks last;
- offer to search/add the high-confidence subset next.
