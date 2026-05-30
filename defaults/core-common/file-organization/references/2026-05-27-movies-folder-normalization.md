# 2026-05-27 — Movies Folder Normalization Pattern

## Trigger

Use this when organizing `D:\Movies` so each movie is stored in its own Plex-friendly folder.

## Target shape

```text
D:\Movies\Movie Title (Year)\<media files>
```

Example:

```text
D:\Movies\Alien Romulus (2024)\Alien Romulus (2024) [720p] [BluRay].mp4
```

## Safe workflow

1. Scan `D:\Movies` top-level entries first.
2. Generate a manifest before moving:
   - source
   - destination folder
   - destination path
   - parse reason
   - status: `ready`, `collision_review_required`, `review_required`, `source_missing`
3. Move only `ready` entries.
4. Create a restore script from actual moved results, not only planned moves.
5. Verify after execution:
   - top-level loose video count
   - collision skips
   - failed moves
   - remaining review items
6. Bundle manifest, results, report, and restore script as an artifact.

## Parsing rules

- Prefer title/year from the filename or existing folder name.
- Normalize only when a year is confidently present: `19xx` or `20xx`.
- Strip common release tokens only after extracting title/year:
  - resolution: `480p`, `720p`, `1080p`, `2160p`
  - source/codec: `BluRay`, `WEBRip`, `WEB-DL`, `x264`, `x265`, `HEVC`, `AV1`
  - groups/noise: `YTS`, `YIFY`, `RARBG`, `TGx`, `GalaxyRG`, etc.
- Preserve readable title case and human punctuation when known, e.g. `2001: A Space Odyssey (1968)`.

## Pitfalls

- Do not invent years. If a loose file lacks a reliable year, leave it in review.
- Do not overwrite collisions. Skip and report them.
- Do not treat documentaries, TV specials, concert films, and odd files as normal movies unless title/year is clear.
- Filename-only parsing is useful but not authoritative. Keep artifacts so mistakes can be reversed.
- Some top-level entries may be non-movie debris or documentaries; examples from this run included ambiguous files like `Man In between.avi` and a National Geographic Alien Moon file. These require manual classification.

## Verification snippet

After execution, verify at minimum:

```powershell
Get-ChildItem -LiteralPath "D:\Movies" -File |
  Where-Object { $_.Extension -match '(?i)^\.(mkv|mp4|avi|mov|m4v|wmv|webm|ts)$' } |
  Select-Object Name
```

Zero loose files is the ideal, but `review_required` loose files are safer than fake folders.
