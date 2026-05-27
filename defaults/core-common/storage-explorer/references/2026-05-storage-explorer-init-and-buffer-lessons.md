# Storage Explorer Session Lessons — 2026-05

## Trigger
Xan corrected the storage-inspection workflow after `D:\Buffer & Backups` full recursive scans dragged and produced little useful progress.

## Durable Lessons

- Default to bounded, programmatic drilldowns for large drive/folder inspection.
- Do not start with a full recursive crawl on backup-heavy trees with hundreds of thousands of tiny files.
- For large roots, first inspect immediate children and apply per-child timeouts/budgets.
- Use stale maps as hints only; verify likely candidates live before recommending deletion.
- Background full scans are acceptable only when clearly useful and should report ETA/rate/progress.
- For user-facing visuals, produce one primary programmatic pie/donut chart by default.
- Use bar charts only for explicit comparisons/rankings.
- Use graphs for relationships between values.
- Do not use NanoBanana for factual scan charts; reserve it for requested explainer infographics.
- `storage-explorer` supersedes the old `file-light-inspection` and `drive-mapper` skills.
- Init/bootstrap child-safe packages should transplant `storage-explorer` as the shared storage situational-awareness skill, not the retired storage skills.

## Safety

- Recycle bin and generated Plex versions can be deletion candidates when explicitly approved.
- Backup folders, personal media, phone backups, and family media remain review-first.
- Exact duplicate deletion requires hash verification.
- Never delete inside large backup roots purely from path name heuristics.
