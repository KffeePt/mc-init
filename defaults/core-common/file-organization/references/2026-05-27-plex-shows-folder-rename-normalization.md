# 2026-05-27 — Plex Shows Folder Rename + Season Normalization

## Trigger

Use this when Xan asks to clean/rename a Plex TV library after torrent imports: top-level show folders contain release noise (`Season 1-7`, `1080p`, codec/group tags), second-level folders are mixed (`S1`, `Season 01`, torrent pack folders), or loose episode files sit at the show root.

## Durable Pattern

1. **Use Plex metadata as the authority for top-level title/year when possible.**
   - Query the live Plex Shows section and read each show `Location` so physical folders map to Plex title/year.
   - On Xan's server, Plex may be reachable from WSL via the Windows host gateway even when `localhost:32400` is refused. From PowerShell on Windows, `localhost:32400` worked; from WSL, use the Windows gateway IP if needed.
   - Do not hardcode section IDs without checking. Live sections observed this run: `1=Movies`, `2=Shows`, `5=Música`, `4=Edits`.

2. **Generate a manifest before mutation.**
   - Save under `Documents/Hermes/Artifacts/YYYY-MM-DD/HH-MM-SS/Shows Folder Rename/`.
   - Include `Rename Manifest.json`, `Top Folder Renames.csv`, `Season Folder Renames.csv`, `Review Items.json`, and `Restore Renames.ps1`.
   - Split statuses: `ready`, `noop`, `collision_review_required`, `source_missing`.

3. **Top-level naming policy.**
   - Target shape: `Show Title (Year)`.
   - Remove torrent/release suffixes such as `Season 1-7`, `S01-S07`, `COMPLETE`, `1080p`, codec tags, release groups, and tracker tags by using Plex title/year rather than regex guessing.
   - Handle Windows case-only rename via a temp intermediate folder; Windows may treat `In` vs `in` as the same path.

4. **Second-level naming policy.**
   - Target shape: `Season N (Year)` and `Specials (Year)`.
   - Infer the year from Plex episode dates when available; otherwise use a known fallback table or the show year for single-season shows.
   - Rename direct season folders first, then flatten malformed torrent-pack folders into the correct season target.
   - Collision behavior: never overwrite. If duplicate content is byte-identical/hash-identical, remove the duplicate source; otherwise suffix the moved filename.

5. **Flatten loose/malformed material.**
   - If a second-level folder name contains explicit season markers (`S01`, `Season 1`, `T01`), move its files into the corresponding `Season N (Year)` folder and remove empty source folders.
   - If top-level episode files contain `SxxEyy`, move them into the matching season folder.
   - Delete only obvious torrent/readme junk (`Downloaded from`, `torrentgalaxy`, `TGx`, `ReadMe`, uploader ads) when clearly non-media; leave artwork/metadata and ambiguous non-episode files in place.
   - Do not force movie-shaped folders into fake season folders. Example from this run: `Free LSD (2023)` remained under Shows as a separate follow-up item rather than being misrepresented as TV.

6. **Patch automation after manual normalization.**
   - If qBittorrent/Plex flatten hooks exist, update them to create/reuse `Season N (Year)` folders instead of `S1`/`S2`, otherwise new downloads regress the tree.
   - Add a helper like `Get-SeasonFolderName(showRoot, seasonNumber)` that reuses existing `Season N (YYYY)` folders and falls back to the top-level show year.
   - Keep the hard refusal to flatten the whole `D:\Shows` root.

7. **Verify after execution.**
   - Check every top-level folder ends with `(Year)`.
   - Check every second-level directory matches `Season N (Year)` or `Specials (Year)`.
   - Check no top-level episode files remain.
   - Check no obvious top-level torrent/readme junk remains.
   - Refresh Plex Shows and report HTTP status.

## Pitfalls

- Plex season XML may not carry useful `year` fields; episode `originallyAvailableAt` is better when present.
- Long-running anime season years can be messy. Prefer not to invent perfect semantics; use Plex/known fallback and report limitations.
- Restore scripts can reverse planned folder renames, but cannot perfectly undo later file-level flatten/merge cleanup. Say that plainly.
- Massive recursive hash checks can time out. For collision handling, hash only exact target/source collisions instead of scanning the whole library.
- PowerShell from WSL and Python from WSL see different network surfaces; localhost for Plex is not guaranteed from WSL.
