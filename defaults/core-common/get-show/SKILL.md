---
name: get-show
description: "Use when Xan asks to download, find, search for, or get a TV show / series / season / episode. Searches multiple public media indexers, detects bundled packs vs loose episodes, presents options with trust levels, and downloads via qBittorrent."
version: 3.4.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [tv-show, series, download, media-index, qbittorrent, media, episodes]
    related_skills: [get-movie, media-transcoding-ffmpeg]
---

# Get Show — Multi-Source Media Search & Download (TV/Series)

## Overview

Searches **multiple public media indexers** for a TV show/series, **automatically classifying results into two categories** — **Bundled Packs** (complete seasons/series) and **Loose Episodes** (individual episodes) — presents all options with metadata and trust levels, then downloads via qBittorrent to `D:\\Shows\\` on BIGGIE.

**Sources (in priority order):**
1. **BitSearch.to** — Primary. HTML-based, no Cloudflare, reliable, good metadata.
2. **apibay.org** — Fallback. Pirate Bay API. Category filtering unreliable (use `cat=0`). Good for season bundles.

**Shared search library:** `/home/xantastique/.hermes/skills/media/lib/` (modular OOP)
**CLI entrypoint:** `/home/xantastique/.hermes/skills/media/media_search.py`

**Drive mapping:**
- **BIGGIE** → `D:\\Shows\\` (TV shows — sole active library after MAMBA/More Shows consolidation) + `D:\\Movies\\` (movies) + `D:\\Music\\` (music)
- **MAMBA (F:\\)** → deprecated; consolidated into BIGGIE D:\\Shows. Do **not** use for new downloads.
- **Archived Shows** → previous show library moved aside for inspection; found on disk as `D:\\Archied Shows\\` (misspelled); check for duplicates/history, but do not download new shows there

**Sort preference:** 1080p first, then highest resolution, then lowest size. 1080p is the sweet spot.

**Note:** YTS is movie-only and not used for TV searches. EZTV API is broken (ignores search params).

## When to Use

- Xan asks to download or find a TV show, series, season, or episodes
- Xan says "get me [show]" / "download [show] season X" / "find the latest [show]"
- Any request implying TV series acquisition

**Don't use for:** Movies → use `get-movie` instead.

---

## Step 0 — Library Pre-Check (MANDATORY)

**Before searching anything, always check if Xan already has the show/season/episode.**

```python
import os, re

SHOWS_DIR = "/mnt/d/Shows/"
ARCHIVED_SHOWS_DIR = "/mnt/d/Archied Shows/"  # inspection only; actual folder is misspelled on disk; do not download here
query_name = "show name here"

if os.path.exists(SHOWS_DIR):
    existing = []
    for root, dirs, files in os.walk(SHOWS_DIR):
        for d in dirs:
            dl = d.lower()
            query_terms = query_name.split()
            if all(term in dl for term in query_terms if len(term) > 2):
                full_path = os.path.join(root, d)
                file_count = len([f for f in os.listdir(full_path) if os.path.isfile(os.path.join(full_path, f))])
                existing.append((d, full_path, file_count))
        for f in files:
            fl = f.lower()
            query_terms = query_name.split()
            if all(term in fl for term in query_terms if len(term) > 2):
                existing.append((f, os.path.join(root, f), 1))

    if existing:
        print("ALREADY IN LIBRARY:")
        for name, path, count in existing:
            print(f"  {name} ({count} items) @ {path}")
    else:
        print("Not found in library -- proceeding with search...")
```

**Rules:**
- Always run this check FIRST
- Search recursively through active `D:\\Shows\\`
- For requested batches, verify every requested show folder exists exactly once before adding anything. Empty folders are not proof of possession; report them as existing-but-empty.
- Scan requested show folders for duplicate episode codes (`S##E##`) before adding gap-fills. If duplicates exist, report them and do not delete until a hash/quality policy is selected.
- If relevant, also note matches under `D:\\Archied Shows\\` as archived/inspection-only, not as the target download library
- MAMBA (`F:\\Shows`) is deprecated — only check for historical reference if needed
- If Xan already has some seasons, note the gap and offer to fill it

---

## Step 1 — Search Using media_search.py

Run the shared search script with `--type show`:

**For bundles (seasons, complete series):**
```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py \
  --type show \
  --query "Show Name Season 1" \
  --limit 25
```

**For complete series:**
```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py \
  --type show \
  --query "Show Name Complete" \
  --limit 25
```

**For specific episodes:**
```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py \
  --type show \
  --query "Show Name S05E01" \
  --limit 25
```

For JSON output:
```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py search \
  --type show \
  --query "Show Name" \
  --limit 25 \
  --json
```

**Query tips:**
- **For bundles/packs:** Include `season`, `complete`, `S##`, or bundle keywords
  - `"Breaking Bad Season 5"` → finds S05 complete packs
  - `"Friends Complete"` → finds full series bundles
  - `"The Office S01"` → finds Season 1 bundles
- **For individual episodes:** Use show name + episode code
  - `"Breaking Bad S05E01"` → finds that specific episode
  - `"Severance S02E03"` → finds that specific episode
- Use show name + year if ambiguous: `"The Office 2005"` vs `"The Office UK"`
- If no results, broaden query (remove year, use shorter name, add "season")

**How the script filters for TV:**
Results are filtered to only include entries matching TV patterns:
- `S##E##` patterns (S01E01, S02E07)
- `Season \d+` patterns
- `S##-S##` multi-season ranges
- `COMPLETE SEASON/SERIES` keywords
- `E##-E##` episode ranges

Game results (FitGirl, CODEX, RUNE, Repack, etc.) are automatically excluded.

---

## Step 2 — Classify: Bundled vs Loose Episodes

**This is the critical differentiation step.** Every result must be classified into one of two types:

### Type A: Bundled Pack

A single torrent containing multiple episodes/seasons.

**Detection patterns** (match ANY):
```regex
(?i)(complete|full|season|s\d{2}\s*[-–]\s*s?\d{2}|all\s*episodes|part\s*\d|ep\s*\d+\s*[-–]\s*ep\s*\d+|1\s*-\s*\d+|\d+\s*of\s*\d+|collection|pack|batch|omnibus)
```

**Sub-classify bundled results by scope:**

| Scope | Pattern | Example |
|---|---|---|
| **Single Season** | `Season \d` / `S\d{2}` alone | "Peacemaker S02 COMPLETE" |
| **Multi-Season** | `S\d{2}-S\d{2}` / `Season \d-\d` | "The Boys S01-S04" |
| **Full Series** | `Complete Series` / `S01 onwards` | "Friends S01-S10 Complete" |
| **Partial Pack** | `Part \d` / `E01-E06` | "Stranger Things S05 Part 1" |

### Type B: Loose Episode

A single torrent containing one individual episode.

**Detection patterns** (match ANY):
```regex
(?i)(s\d{2}e\d{2}|season\s*\d+\s*episode\s*\d+|ep\.?\s*\d+|e\d{2}(?!\s*[-–]))
```

---

## Step 3 — Present Options to Xan

**Always present BOTH categories separately. Bundled first, then loose.**

```
📺 <Show Name> — Search Results
Sources: 2/2 active | 25 results

===== BUNDLED PACKS =====

 # | Scope          | Resolution | Format     | Size    | S:L    | Trust | Group
---|----------------|-----------|------------|---------|--------|-------|-------
 1 | Full S01-S05   | 1080p     | BluRay x265| 140 GiB | 217:755| 🟢★★★ | afm72
 2 | S01 Only       | 720p      | BRRip      | 2.71 GiB| 254:206| 🟠★★☆ | Sujaidr
 3 | S05 Complete   | 720p      | BRRip      | 5.99 GiB| 224:277| 🟠★★☆ | Sujaidr

===== LOOSE EPISODES =====

 # | Episode      | Resolution | Format     | Size    | S:L    | Trust | Group
---|-------------|-----------|------------|---------|--------|-------|------
 4 | S02E03      | 1080p     | WEB-DL x264| 1.51 GiB| 3134:3294| 🟢★★★| FLUX
 5 | S02E02      | 1080p     | HEVC x265  | 832 MiB | 2610:2450| 🟠★★☆| MeGusta
 6 | S02E01      | 1080p     | x265       | 1.15 GiB| 2216:1153| 🟢★★★| ELiTE
```

**Key presentation rules:**
- **Bundled packs ALWAYS shown first** — they are usually the better choice
- Within each section: sort by **Trust desc → Seeders desc → Resolution desc**
- Show **at least top 5 bundled + top 8 loose**
- Group loose episodes by season/episode order
- Note source as **public media index**

---

## Step 4 — Download via qBittorrent

### Destination Directory

**TV shows go to `D:\\Shows\\<ShowName>\\` on BIGGIE**

### Folder Organization — Flat Season Structure

**Xan's rule:** Show folders must be tidy. No nested subfolders with the show name repeated inside itself.

Required structure:

```
D:\Shows\YOU\           ← One clean show folder
├── S1\                  ← Season folders directly inside
│   ├── S01E01.mkv
│   └── ...
├── S2\
│   ├── S02E01.mkv
│   └── ...
├── S3\
├── S4\
└── S5\
```

NOT this:

```
D:\Shows\YOU\YOU S01-S04\Season 1\...   ← WRONG: nested show-name subfolder
D:\Shows\YOU\YOU S01\...                ← WRONG: torrent pack folder as-is
```

**How to achieve this:**

Torrents arrive with their own internal folder structure (e.g., `You.S01-S04.1080p.x265-PSA/Season 1/...`). Setting qBittorrent `savepath` to `D:\Shows\YOU\` will create `D:\Shows\YOU\You.S01-S04.1080p.x265-PSA\`, which is **wrong**.

Instead:

1. Set qBittorrent `savepath` to `D:\Shows\YOU\` for both torrents. This is the download landing zone.
2. **After download completes**, reorganize into flat `S1/`, `S2/`, `S3/`, etc. inside `D:\Shows\YOU\`.
3. After reorganization, delete the empty torrent-pack wrapper folders.
4. If qBittorrent is seeding from the reorganized files, use `torrents/setLocation` to point each torrent at the new flat season paths. If that breaks seeding, note it — Xan may prefer tidy folders over continued seeding.

**Post-download flattener (run after all downloads complete):**

```bash
# Scan D:\Shows\YOU\ for S##E## files, group by season, move into S1/S2/...
python3 ~/.hermes/skills/media/media_search.py flatten --path "/mnt/d/Shows/YOU/"
```

When presenting download options, always note whether post-download flattening will be needed and flag if torrents contain nested structures.

### qBittorrent Web UI Connection

**Configuration:**
- **Path:** `C:\Program Files\qBittorrent\qBittorrent.exe`
- **Web UI port:** 8080
- **Credentials:** `$QBITTORRENT_USERNAME` / `$QBITTORRENT_PASSWORD` (or local qBittorrent config; never hardcode credentials in skills)
- **API base:** `http://localhost:8080/api/v2`

#### Auth

```bash
# Login and save session cookie
curl -s "http://localhost:8080/api/v2/auth/login" \
  --data-urlencode "username=$QBITTORRENT_USERNAME" \
  --data-urlencode "password=$QBITTORRENT_PASSWORD" \
  -c /tmp/qb_cookies.txt
```

#### Add Torrent (Magnet Link)

```bash
curl -b /tmp/qb_cookies.txt \
  "http://localhost:8080/api/v2/torrents/add" \
  --data-urlencode "urls=$MAGNET_LINK" \
  --data-urlencode "savepath=D:\\Shows\\<ShowName>\\"
```

Response:
```json
{
  "added_torrent_ids": ["abc123..."],
  "failure_count": 0,
  "pending_count": 0,
  "success_count": 1
}
```

### Download Scenarios

#### Scenario A: Single Bundle Selected
Add one torrent, set path to `D:\Shows\<ShowName>`. Done.

#### Scenario B: Multiple Loose Episodes (Batch Download)
```bash
for ep_name, magnet in eps_to_download:
  add_to_qbittorrent(magnet, download_dir="D:\\Shows\\<ShowName>\\")
  sleep 1  # Rate-limit
```

**Recursive download mode** ("download everything" / "get all episodes"):
1. Collect ALL loose episode magnets
2. Deduplicate by S##E## (keep highest trust)
3. Add each to qBittorrent sequentially with 1s delay
4. Report: "Added 8/8 episodes from S05 to qBittorrent"

#### Scenario D: Bundle Replaces Existing Individual Episodes

When a bundle download covers seasons that already have individual/episodic files:

1. **Verify the bundle is a superset** — confirm the bundle contains the same seasons with ≥ episode count of what's already on disk
2. **Delete old content before the bundle finishes** — remove the old nested season folders/files so the completion hook doesn't conflict
3. **Only delete if confirmed replaceable** — same season number, same or higher episode count. If the bundle is incomplete vs existing, warn and keep both
4. **Delete the old folders immediately after verifying the bundle's file list**, don't wait for completion
5. If uncertain, keep both and let the flatten hook handle dedup — Xan can clean up later

**Example:** Smiling Friends had S01E01-E07 from individual downloads. S01-S03 complete bundle confirmed S01 had all 9 episodes. Deleted old `Smiling.Friends.S01.1080p.WEBRip...` folder immediately after bundle partial download confirmed S01 contents.

---

## Download Status

When Xan asks about download status or if a download is done:

```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py status
python3 /home/xantastique/.hermes/skills/media/media_search.py status --filter "Breaking Bad"
```

Returns progress %, speed, ETA, seeds/peers for each torrent in qBittorrent.

**Prerequisite:** qBittorrent Web UI must be running. If it fails with "not accessible", start qBittorrent:
```bash
"C:\Program Files\qBittorrent\qBittorrent.exe" &
```

---

## Post-Download Automation — Flatten + Plex Refresh (qBittorrent Completion Hook)

Xan wants post-download automation: **flatten nested torrent pack folders into flat season structure, then refresh Plex.** Over-refreshing is fine — multiple completions should each trigger.

### What the hook script does

Two scripts deployed at `C:\\Users\\santi\\Documents\\Hermes\\Scripts\\`:

1. **`qbittorrent-on-added.ps1`** — logs torrent additions to `qbittorrent-on-added.log`, maintains `qbittorrent-active.json` state file (Wilson reads this for situational awareness without polling qBittorrent API).
2. **`qbittorrent-on-finished.ps1`** — marks completions in active.json, refreshes live qBittorrent telemetry, computes size/speed/ETA/seed reliability, decides whether to wait for near-finished torrents or flush completed groups, flattens nested pack folders into canonical `Season N (Year)` folders, moves sidecar files, removes empty dirs, refreshes the active Plex Shows section (currently section 2).

The on-finished script handles:

1. **Flattening** — finds `S##E##` video files in nested pack folders, copies/moves them into canonical `Season N (Year)` folders. Automatically sanitizes filenames on the fly by stripping URLs (e.g., `www.UIndex.org`) and bracketed release tags (`[EZTVx.to]`). Non-video audio extras are not treated as episodes.
2. **Sidecar files** — `.srt`, `.sub`, `.nfo`, etc. are moved alongside their matched episodes
3. **Review queue for collisions** — if a new/remote completed file collides with an existing local library file and hashes differ, the hook defaults to keeping the new/remote media in Plex, moves the old/local media into `D:\Review\YYYY-MM-DD\HH-MM-SS\`, exposes a current hardlink/copy under `D:\Review\current\`, and rewrites `D:\Review\current\review.yaml`. Xan can run `C:\Users\santi\Desktop\smart_org.bat` for a TUI: `remote` keeps the new file (default), `local` restores the old file, and `merge` keeps both with `old -` / `new -` prefixes.
4. **Cleanup** — removes empty leftover nested folders
5. **Plex refresh** — triggers refresh of the consolidated D:\Shows library (section mapping may need verification post-consolidation; legacy sections 2 + 6 are deprecated)

The current smart on-finished script removes completed qBittorrent torrents with `deleteFiles=false` before flattening, then uses `Move-Item` into canonical season folders. This avoids seed-lock copy timeouts while keeping downloaded files. Logs to `qbittorrent-on-finished.log` in the same Scripts directory. Manual runner: `C:\Users\santi\Desktop\smart_org.bat`; legacy alias: `C:\Users\santi\Desktop\WILSON_Hash_Verify.bat` now runs the same smart organizer instead of hash-only verification.

### One-Time Setup

1. Scripts already deployed at `C:\\Users\\santi\\Documents\\Hermes\\Scripts\\`
2. In qBittorrent GUI: **Tools → Options → Downloads** → check **both**:
   - "Run external program on torrent added":
     ```
     powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\santi\Documents\Hermes\Scripts\qbittorrent-on-added.ps1" "%F" "%N" "%L" "%D"
     ```
   - "Run external program on torrent completion":
     ```
     powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\santi\Documents\Hermes\Scripts\qbittorrent-on-finished.ps1" "%F" "%N" "%L" "%D"
     ```

Both scripts are idempotent — safe to re-run on already-flattened folders. The active.json state file lets Wilson check download queue without API polling.

### Plex Token & Section Mapping

Full reference: `references/plex-token-and-sections.md`

Quick lookup:
- Section 1: Movies → `D:\Movies\`
- **D:\Shows library** → consolidated; verify current Plex section mapping via token retrieval
- Token: retrieve from `HKCU:\Software\Plex, Inc.\Plex Media Server` → `PlexOnlineToken`

**Note:** Legacy sections 2 (MAMBA `F:\Shows`) and 6 (old `More Shows`) are deprecated post-consolidation. Only one active Shows library maps to `D:\Shows`.

### PowerShell-through-WSL Pitfalls

Full reference: `references/powershell-wsl-pitfalls.md`

Key rules when scripting PowerShell from WSL:
- Use `Copy-Item -LiteralPath`, never `Move-Item` on qBittorrent-seeded files
- Don't use `robocopy` from the WSL→PowerShell chain — path quoting breaks
- Verify scripts after writing with `[Parser]::ParseFile()` to catch heredoc backslash doubling
- Single-quote PowerShell commands from bash to prevent `$` variable expansion

---

## Malware Scan

After a download completes, scan the target directory:

```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py scan --path /mnt/d/Shows/
python3 /home/xantastique/.hermes/skills/media/media_search.py scan --path /mnt/d/Shows/ShowName/
```

Three-layer scan:
1. **Extension check** — flags .exe, .bat, .dll, .ps1, .scr, .iso, etc. as HIGH severity
2. **Metadata check** — detects embedded PE executables in media files (CRITICAL), suspiciously small media files (MEDIUM)
3. **Windows Defender** — runs `Start-MpScan` on the directory via PowerShell

Verdict: SAFE (no critical/high issues) or ISSUES FOUND with severity breakdown.

---

## Gap Analysis — Missing Episodes & Existing Status

**Analyze what you have vs what's missing for any show in your library.**

```bash
# Check what episodes are missing for a show
python3 /home/xantastique/.hermes/skills/media/media_search.py gap \
  --type show --query "Breaking Bad"

# Also search for missing episodes on indexers
python3 /home/xantastique/.hermes/skills/media/media_search.py gap \
  --type show --query "Mr Robot" --search-missing

# JSON output for programmatic use
python3 /home/xantastique/.hermes/skills/media/media_search.py gap \
  --type show --query "Severance" --json

# Override default library path
python3 /home/xantastique/.hermes/skills/media/media_search.py gap \
  --type show --query "The Bear" --library "/mnt/d/Shows/"
```

**Output example:**
```
📺 Mr. Robot — Gap Analysis [TVmaze]
Status: Ended | Episodes: 32/45 (71.1%)

===== SEASON SUMMARY =====
  Season 01: ████████████████████ 100% (10/10, 0 missing)
  Season 02: ████████████████████ 100% (12/12, 0 missing)
  Season 03: ░░░░░░░░░░░░░░░░░░░░ 0% (0/10, 10 missing)
  Season 04: ███████████████░░░░░ 77% (10/13, 3 missing)

===== MISSING EPISODES =====
  Season 3:
    ❌ S03E01 eps3.0_power-saver-mode.h — 2017-10-11
    ❌ S03E02 eps3.1_undo.gz — 2017-10-18
    ...

===== EXISTING EPISODES =====
  ✅ S01E01  S01E02  S01E03  ...
```

**With `--search-missing`**, also searches for torrents for each missing episode (individually or by season bundle).

**Data source:** TVmaze (free, no API key). Scans `D:\Shows\` for S##E## patterns in filenames.

**Flexible episode pattern matching:**
The scanner uses multi-pattern regex to handle various Plex-compatible naming conventions:
- `S01E01`, `s01e01` (standard)
- `S1_E1`, `S3_E10` (underscore separator)
- `S1x1`, `1x01` (x separator)
- `Season 1 Episode 1` (word-based)

First finds the show's base directory via fuzzy matching (60% word overlap threshold), then scans recursively for all matching patterns regardless of subdirectory structure.

### When to use gap analysis

- Xan asks "what episodes am I missing of [show]"
- Xan asks "do I have all seasons of [show]"
- Xan asks to fill gaps in an existing show
- Xan asks what shows in the whole library are behind, missing new seasons, or not up to date by a cutoff date
- After downloading a bundle, to verify completeness
- Before searching, to know which episodes to look for

### Library-wide gap audits

For whole-library audits, scan every active `D:\\Shows` folder, resolve against TVMaze using the folder title/year, and split results into three buckets:

1. **High-confidence recent/new-season gaps** — safe candidates to search/add next.
2. **Older backlog gaps** — real incompleteness, but not necessarily urgent.
3. **Manual-review / unsafe matches** — anime season-numbering mismatches, anthologies, zero matched local episode codes, or weak/wrong TVMaze matches.

Do not auto-fill from the manual-review bucket. Write raw JSON plus a concise human report so Xan sees the actionable list first. See `references/2026-05-27-library-wide-gap-audit.md` for the session-tested pattern and false-positive traps.

---

## Complete Workflow

```
0. Receive show name (+ optional season/episode spec) from Xan
1. LIBRARY PRE-CHECK: Scan active `D:\\Shows\\` recursively; also inspect archive `D:\\Archied Shows\\` for existing copies before downloading (MAMBA F:\ is deprecated)
1a. If show exists: run GAP ANALYSIS to identify missing episodes
2. Run: python3 media_search.py search --type show --query "Show Name" --limit 25
   OR: python3 media_search.py gap --type show --query "Show Name" --search-missing
3. CLASSIFY each result → bundled pack OR loose episode
4. Present options in TWO SECTIONS: BUNDLED PACKS, then LOOSE EPISODES
5. Wait for Xan's selection(s)
5a. If Xan says "ok that is it", "grab option N", "add it", or similar, treat this as explicit selection of the last recommended/listed option. Do not switch tasks, create unrelated artifacts, or ask for reconfirmation unless the prior option mapping is genuinely unavailable.
6. Resolve magnet links from selected results
7. Ensure qBittorrent running, login via API
7a. BUNDLE OVERLAP CHECK: If a bundle covers seasons with existing individual episodes, verify the bundle is a superset (same seasons, ≥ episode count), then delete the old content before the bundle finishes
8. Submit each torrent to `D:\\Shows\\<Show Name>\\` with an explicit show media type/category (`--type show` when using `add_and_watch.py` or `media_search.py add`) so qBittorrent stores category `tv` and the hooks route it into the Shows batch flattener.
9. Batch downloads: 1s delay between submissions, deduplicate episodes
10. Verify all torrents in active list
11. Report summary including sizes, destination, and that post-download flattening + Plex refresh are pending
12. After downloads complete, do **not** trust watcher completion alone. Verify actual folder shape under `D:\Shows\<Show Title (Year)>`: no root-level episode files and no torrent wrapper directories.
13. Flatten/organize into canonical `Season N (Year)` folders. If the qBittorrent PowerShell hook did not run or did not log the real torrent names, run a manual flatten/organize pass before claiming success.
13a. If duplicate `S##E##` groups or `__COLLISION_REVIEW` files remain after flattening, apply the explicit replacement policy before reporting success. When Xan says to keep newly downloaded media, prefer the new/remote download using collision metadata first, then mtime/release markers/expected quality as secondary evidence. Move old/collision loser files outside Plex into `D:\\HermesCleanup\\...` or the configured review/archive location with a manifest; do not hard-delete unless explicitly asked.
13b. Preserve no-code Specials unless they are explicitly in scope. They are not direct episode-code collisions and may need a separate Plex-ordering review.
13c. For “smart flattener worked?” verification, do not stop at qBittorrent completion or an empty torrent list. Inspect canonical season folders, audit duplicate episode codes, check collision/review markers/manifests, apply the explicit keep-new/keep-old policy, then re-audit before refreshing Plex.
14. Run malware scan on the show directory
15. Trigger Plex refresh for the consolidated D:\Shows library


See `references/requested-show-batch-gap-fill.md` for the workflow when Xan provides a multi-show list, asks which shows/seasons are actually missing, then asks to download every missing show: audit first, exact-title validate, add with `--type show`, verify qBittorrent category/path, and record overlap cleanup risks.
See `references/qbittorrent-watchers-vs-flatten-hooks.md` for the important distinction between watcher completion and actual folder flattening; always verify filesystem shape before claiming show organization succeeded.
See `references/post-flatten-collision-cleanup.md` for the replacement-bundle/collision-review cleanup pattern: keep newly downloaded media when requested, move loser files out of Plex with a manifest, then re-audit duplicates before refreshing Plex.
See `references/smart-flattener-collision-verification.md` for the exact verification sequence when Xan asks whether the smart flattener worked after all downloads complete, especially with an explicit keep-new collision policy.
See `references/selection-followthrough.md` for preserving option context across turns.
See `references/qbittorrent-status-fallback.md` for the WSL-to-Windows PowerShell fallback for qBittorrent status.
See `references/plex-section-single-copy-cleanup.md` for Plex `Shows` vs `More Shows` single-copy cleanup.
See `references/plex-token-and-sections.md` for Plex API token retrieval and section mapping.
See `references/powershell-wsl-pitfalls.md` for Copy-Item-over-robocopy, heredoc backslash bugs, and WSL→PowerShell quoting rules.
See `references/qbittorrent-event-hooks.md` for the canonical shared-Hermes script location, qBittorrent GUI commands, state/log files, relocation checks, and event-driven hook behavior.
See `templates/qbittorrent-flatten-refresh.ps1` for the original qBittorrent completion hook script template (flatten + Plex refresh). The deployed production versions are `qbittorrent-on-added.ps1` and `qbittorrent-on-finished.ps1` at `C:\Users\santi\Documents\Hermes\Scripts\`.

---

## Code Architecture

The search system uses a modular OOP design under `lib/`:

```
lib/
├── search/          # Indexer implementations (BaseSearcher ABC)
│   ├── bitsearch.py # BitSearchSearcher
│   ├── yts.py       # YTSSearcher (movies only)
│   ├── apibay.py    # ApiBaySearcher
│   └── engine.py    # SearchEngine (orchestrator)
├── filters/         # Media type classifiers (BaseFilter ABC)
│   ├── movie.py     # MovieFilter
│   ├── show.py      # ShowFilter
│   └── music.py     # MusicFilter
├── metadata/        # Metadata extraction + TrustClassifier
├── gap/             # Gap analysis (BaseGapAnalyzer ABC)
│   ├── base.py      # GapResult, BaseGapAnalyzer
│   ├── show.py      # ShowGapAnalyzer (TVmaze API)
│   ├── music.py     # MusicGapAnalyzer (MusicBrainz API)
│   └── movie.py     # MovieGapAnalyzer (Cinemagoer + heuristic)
├── qbittorrent/     # QBittorrentClient (PowerShell bridge)
├── scanner/         # MalwareScanner
└── formatters/      # ResultFormatter, StatusFormatter, ScanFormatter, GapFormatter
```

---

## Known Issues & Pitfalls

1. **EZTV API search is broken.** The search/query parameters are ignored — always returns latest global uploads. Only `imdb_id` works but requires prior knowledge. Not used in the search script.

2. **apibay category IDs are unreliable for TV.** TV shows appear in cat 205, 207, 208, 210, etc. Always use `cat=0` and filter by content pattern.

3. **1337x is Cloudflare-blocked.** Cannot scrape without browser automation.

4. **BitSearch.to is the most reliable source.** No Cloudflare, good metadata, HTML-entity-encoded magnets decoded automatically by the script.

5. **Misclassifying a result.** A result named "Show S01" could be a single season bundle OR poorly labeled. Check `num_files` from apibay (>1 = likely bundle). BitSearch doesn't expose file count directly.

6. **Same episode multiple times.** Different release groups upload the same episode. When doing batch downloads, deduplicate by S##E##, keeping highest-trust option.

7. **Bundle + loose overlap.** If Xan selects both a bundle containing S01E01-S01E10 AND individually selects S01E05, warn about overlap.

8. **Show name ambiguity.** "The Office" could be US or UK. Present grouped by apparent show and ask Xan to clarify.

9. **Incomplete season packs.** Packs uploaded mid-season may be incomplete. Flag as POTENTIALLY INCOMPLETE if uploaded before season end date.

10. **qBittorrent API rate limiting.** Add 1-2 second delays between batch submissions.

11. **qBittorrent add can return HTTP 204 without the torrent appearing.** Always verify via `torrents/info` after adding. If `media_search.py add` reports success but verification fails, retry with a native PowerShell `Invoke-WebRequest` body hashtable (`@{urls=$magnet; savepath=$savePath}`) rather than the Python client's string-built body.

12. **If Xan selects a torrent and then asks “anything else remaining?”, check qBittorrent before searching or adding again.** The selected torrent may already be active from a previous/submitted step. Query `torrents/info` by show terms/hash/name, verify `save_path`, `state`, `progress`, seeds/peers, and speed. If it is already active at `D:\\Shows\\<ShowName>`, do **not** re-add it; report remaining work as “wait for completion, then scan/verify Plex.”

13. **qBittorrent status via WSL localhost may fail while Windows localhost works.** If `media_search.py status` or WSL `curl http://localhost:8080/...` fails/parses empty output, query from the Windows host with PowerShell:
```powershell
$base="http://localhost:8080/api/v2"
$s=New-Object Microsoft.PowerShell.Commands.WebRequestSession
Invoke-WebRequest -UseBasicParsing -Uri "$base/auth/login" -Method Post -Body @{username=$env:QBITTORRENT_USERNAME;password=$env:QBITTORRENT_PASSWORD} -WebSession $s
(Invoke-WebRequest -UseBasicParsing -Uri "$base/torrents/info?filter=all" -WebSession $s).Content | ConvertFrom-Json |
  Where-Object { $_.name -match "Show|Terms" } |
  Select-Object name,hash,state,progress,dlspeed,num_seeds,num_leechs,size,save_path
```
Do not encode this as “qBittorrent is broken”; it is a host/WSL loopback context issue. Use the Windows-side API probe as the fallback.

14. **qBittorrent location changes are asynchronous.** When changing a torrent from MAMBA to BIGGIE with `/torrents/setLocation`, qBittorrent may report the old `save_path` while state is `moving`. Poll `torrents/info` until state is no longer `moving`, then verify `save_path`. Do not claim the move succeeded from the initial API response alone.

12. **Existing/legacy torrents may remain in deprecated paths.** Before adding a show, query qBittorrent by name/hash and check active paths. MAMBA (`F:\Shows`) is deprecated — if a matching torrent is still targeting F:\, use qBittorrent `torrents/setLocation` to move it to `D:\Shows\<ShowName>` and verify until state exits `moving` and `save_path` updates.

13. **qBittorrent default save path should be kept aligned with the skill.** After migration or service restart, verify `app/preferences.save_path == D:\Shows`; if not, set it via `app/setPreferences` before adding new shows.

14. **PowerShell through WSL expands `$` unless quoted correctly.** When running PowerShell one-liners from WSL, wrap the whole `-Command` script in single quotes or escape `$` variables; otherwise `$_` becomes a WSL path fragment and produces noisy false failures.

15. **Path length limits on Windows.** Keep show folder names reasonable. Windows MAX_PATH is 260 chars.

16. **Episode scanning false negatives.** The gap analyzer uses multi-pattern regex (S##E##, S#_E#, S#x#, Season # Episode #) but some naming conventions may still not match. If a show appears incomplete but you know it's complete, check the actual filenames — the scanner may need another pattern added.

17. **Cartoon/short-segment shows can make gap analysis look falsely incomplete.** TVMaze often counts individual shorts/segments as separate episodes, while release packs may combine multiple shorts into one Plex-style episode file. For shows like *The Grim Adventures of Billy & Mandy*, do not conclude the torrent is bad solely because TVMaze reports many "missing" segment-level episodes. Cross-check local season folders, file counts, naming, qBittorrent completion, and Plex visibility before recommending gap-fills. For single-copy cleanup in the consolidated D:\Shows library, verify Plex is only seeing the intended copies.

19. **Xan explicitly dislikes "Judas" release groups for anime.** Do NOT prioritize or recommend [Judas] releases as the top option when presenting anime choices. The [Judas] tag is a known release group that the user has rejected. Present non-Judas alternatives first (e.g., [Anime Time], KaNNa, EMBER, ASW, DKB, DiabloTripleA, Andoros) and only include Judas releases as lower-tier options if no viable alternatives exist. If the user explicitly says "NOT judas" or similar, treat it as a hard exclusion.

20. **Copy-Item, not Move-Item, for qBittorrent-seeded files.** qBittorrent holds read handles on completed torrents. `Move-Item` fails with "file in use." `Copy-Item` succeeds, then try `Remove-Item` on the source — if it fails (seed lock), that's fine. During active download (pre-completion), files have exclusive write locks and `Copy-Item` also hangs — but the production hook fires post-completion so this only affects testing.

21. **Don't use robocopy from the WSL→PowerShell chain.** Path quoting through WSL bash → PowerShell → robocopy.exe breaks on spaces in filenames/directories. Use PowerShell-native `Copy-Item -LiteralPath` instead.

22. **PowerShell heredoc backslash doubling from WSL.** When writing .ps1 files via WSL tools, backslashes in regex patterns can get doubled. Always parse-verify with `[Parser]::ParseFile()` after writing.

23. **Short show names are hard to search.** "YOU" matched hundreds of false positives on public indexers. Use show name + year (e.g., "YOU 2018") or season-specific queries. If a name is too generic, search season-by-season instead of "Complete Series."

24. **PowerShell backtick escaping breaks from WSL bash.** When running `powershell.exe -Command "..."` with backtick-escaped variables (e.g., ``` ``n ```, ``` `$ ```), bash interprets the backticks before PowerShell sees them, causing syntax errors. The reliable pattern: write the PowerShell to a temp `.ps1` file and invoke it with `-File`, not `-Command`.

25. **When re-adding a torrent you previously identified, query the indexer directly by release-group name.** `media_search.py` searches multiple indexers and filters — it may miss a torrent you know exists. If you have the release group name from prior context (e.g., "HODL" or "icecracked"), query the specific indexer API directly: `curl -s 'https://apibay.org/q.php?q=Show+Name+RELEASEGROUP&cat=0'`. This finds results the general search pipeline may filter out. Build the magnet from `info_hash` if the API doesn't return a magnet link.

26. **Double-extension malware bait in search results.** Some results spoof trusted group names (FLUX, ETHEL, etc.) but append a second extension: `.mkv.scr`, `.mkv.exe`, `.mkv.scr.exe`. A `.scr` (screensaver) or `.exe` extension after a media extension is malware, not a mislabeled video. Flag these as 🔴 RISKY and exclude from recommendations, even if seed counts look healthy. Legitimate FLUX/ETHEL releases never carry double extensions. Also flag standalone suspicious extensions: `.iso` on a single-episode `.mkv` (`.mkv.iso`).

27. **Dead show on public trackers — when to stop digging.** If 3+ query variants (original name, year, alternative language terms, direct apibay API) all return only 0–3 seeder results with no bundles, the show is effectively dead on public indexers. Recommend: (a) shelve for now, (b) suggest private tracker/Usenet/direct download sources, (c) flag as a candidate for later re-check. Do not keep searching indefinitely — the data isn't going to improve.

28. **Strict title validation before adding.** Public indexers often return high-seed wrong-title bait for short/common show names. Example failure mode: searching `The Bear S04` returned `The Island With Bear Grylls`, which must be rejected even if it superficially contains `Bear` and a season token. Before selecting or adding, require the canonical show title tokens plus the requested season/episode token; if no exact-title result exists, search individual episodes rather than accepting a wrong-series season pack.

29. **Requested-batch precheck includes duplicate detection.** When Xan gives a list of shows/seasons to fetch, first verify every requested show folder exists exactly once under `D:\\Shows`, then scan those folders for duplicate episode codes. Report empty folders separately from missing folders. Do not add torrents until duplicate suspects are either left intentionally or cleaned under a hash/quality policy.

30. **Watcher completion is not flatten verification.** `watch_batch.py` can mark torrents complete, scan, and refresh Plex while files remain at the show root or inside torrent wrapper directories. Current watcher logic must resolve the real media root from qBittorrent `save_path` / `content_path` first, then extract Plex-style identity from folder/filename conventions (`Show Title (Year)` plus `S##E##`) before scan/flatten. Do not rely on fuzzy torrent-title matching; release names are polluted and will miss folders. After every completed show batch, inspect `D:\\Shows\\<Show Title (Year)>` for root-level episodes and non-season wrapper folders. If present, flatten manually or patch the post-completion flow before reporting success. See `references/qbittorrent-watchers-vs-flatten-hooks.md`.

30a. **Post-flatten duplicate/collision cleanup is a separate verification gate.** A hook can remove wrappers and still leave duplicate `S##E##` files, old release-group copies, alternate season-year folders, or `__COLLISION_REVIEW` suffixes. When the replacement policy is clear, especially “keep the newly downloaded media,” prefer the new/remote file using collision metadata before heuristic evidence, move loser files out of Plex into a dated `D:\\HermesCleanup\\...` backup or configured review/archive location with a manifest, then re-audit until duplicate groups and collision leftovers are zero. Preserve no-code Specials unless explicitly in scope. See `references/post-flatten-collision-cleanup.md` and `references/smart-flattener-collision-verification.md`.

31. **Strict all-active batch barriers can block completed shows.** A JSON registry that defers flattening while *any* show torrent remains active is safe but too blunt: one slow download, e.g. a long-tail season pack, can prevent completed roots from being flattened and scanned. Prefer an adaptive scheduler: record size/progress/speed/qBittorrent ETA/seeds/peers per info hash, compute reliability and ETA groups, wait only for near-finished reliable items, and flush completed roots when remaining active items are long-tail or stalled. Never flatten active content paths; rank torrent jobs for scheduling only, not episode files for layout.

---

## Trust Level Classification

Same as `get-movie` — identical system:

| Trust | Indicator | Score |
|---|---|---|
| **🟢 TRUSTED** | VIP/Moderator + known groups | 5/5 stars |
| **🟡 KNOWN** | Trusted/Helper skull | 4/5 stars |
| **🟢 VERIFIED** | No badge but excellent swarm health | 3/5 stars |
| **🟠 ACCEPTABLE** | No badge, moderate seeders | 2/5 stars |
| **🔴 RISKY** | Low seeds, spam signals | 1/5 stars |

**Known safe TV release groups** (auto-TRUSTED):
ETHEL, MEGusta, EDITH, GRACE, BiOMA, RAWR, AMB3R, RMTeam, NTb, FLUX, TGx, HiQVE, PSA, Kitsune, Silence, Panda, t3nzin, Garshasp, afm72, Ghost, BONE, CAKES, SuccessfulCrab, ELiTE, REVILS, higgsboson, playWEB, PCOK, LOOTera, eztv, JFF, mSD, FQM, TORRENTGALAXY, HODL, icecracked

---

## Verification Checklist

- [ ] Library pre-check executed — scanned D:\Shows\ recursively; also noted D:\Archied Shows\ matches if relevant (MAMBA F:\ deprecated)
- [ ] Requested show folder exists exactly once under D:\Shows\, or empty/missing/ambiguous state was reported
- [ ] Duplicate episode-code scan completed for requested show folders before adding gap-fills
- [ ] Search executed via media_search.py with --type show
- [ ] Results filtered for TV-type content only
- [ ] Results classified into bundled vs loose
- [ ] Both sections presented separately with trust indicators
- [ ] Xan confirmed selection(s)
- [ ] Magnet links obtained from results
- [ ] qBittorrent running and Web UI accessible
- Agent-added show torrents must pass `--type show`; `media_search.py add` writes qBittorrent category `tv`, and the qBittorrent hooks require media_type `show` before touching `D:\\Shows`. This prevents movie torrents from delaying or triggering show flattening.
- [ ] Batch downloads rate-limited with 1s delays
- [ ] Duplicate episodes detected and deduplicated
- [ ] qBittorrent completion hook script deployed at `C:\Users\santi\Documents\Hermes\Scripts\qbittorrent-on-finished.ps1` with correct Plex token
- [ ] qBittorrent GUI "Run external program on torrent completion" enabled with the correct command
- [ ] qBittorrent GUI "Run external program on torrent added" enabled with the correct command
- [ ] Post-download flatten verified: flat `S1/`, `S2/`, etc. season folders, no nested pack wrappers
- [ ] Malware scan passed on show directory
- [ ] Plex refresh triggered for consolidated D:\Shows library