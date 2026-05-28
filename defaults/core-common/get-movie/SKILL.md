---
name: get-movie
description: "Use when Xan asks to download, find, search for, or get a movie. Searches multiple public media indexers, presents options with metadata/trust levels, and downloads via qBittorrent."
version: 3.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [movie, download, media-index, qbittorrent, media]
    related_skills: [get-show, media-transcoding-ffmpeg]
---

# Get Movie — Multi-Source Media Search & Download

## Overview

Searches **multiple public media indexers** for available copies of a movie, parses results into a structured options list with **source**, **trust level**, **size**, **format/resolution**, and **seed/leech counts**, then sends the selected torrent to qBittorrent's Web UI for downloading to `D:\\Movies\\`.

**Sources (in priority order):**
1. **BitSearch.to** — Primary. HTML-based, no Cloudflare, reliable, good metadata.
2. **YTS.ag** — Movie enrichment. Verified YTS releases, small sizes, high quality. API endpoint: `https://yts.ag/api/v2/list_movies.json` (requires `-L` for redirects).
3. **apibay.org** — Fallback. Pirate Bay API. Category filtering is unreliable (use `cat=0`). Referer header required.

**Shared search library:** `/home/xantastique/.hermes/skills/media/lib/` (modular OOP)
**CLI entrypoint:** `/home/xantastique/.hermes/skills/media/media_search.py`

**Drive mapping:**
- **BIGGIE** → `D:\\Movies\\` (movies) + `D:\\Music\\` (music)
- **MAMBA** → `F:\\Shows\\` (TV shows)

**Sort preference:** 1080p first, then highest resolution, then lowest size. 1080p is the sweet spot.

## When to Use

- Xan asks to download or find a movie by name
- Xan says "get me [movie]" / "download [movie]" / "find [movie]"
- Any request implying movie acquisition

**Don't use for:** TV shows / series → use `get-show` instead.

---

## Step 0 — Library Pre-Check (MANDATORY)

**Before searching anything, always check if Xan already has the movie.**

```python
import os

MOVIES_DIR = "/mnt/d/Movies/"
query_name = "movie name here"  # lowercase, simplified

if os.path.exists(MOVIES_DIR):
    existing = []
    for entry in os.listdir(MOVIES_DIR):
        el = entry.lower()
        query_terms = query_name.split()
        if all(term in el for term in query_terms if len(term) > 2):
            existing.append(entry)

    if existing:
        print("ALREADY IN LIBRARY:")
        for e in existing:
            print(f"  {e}")
        # Ask Xan: proceed anyway? re-download in different quality?
    else:
        print("Not found in library -- proceeding with search...")
```

**Rules:**
- Always run this check FIRST before any network request
- If a match is found, report it and **ask before proceeding**
- For batch requests, also check normalized-title duplicate suspects at the movie root before adding new downloads; malformed folder names can hide duplicates, e.g. `Title (Year)` versus `Title( (Year)`.
- If Xan already has 4K/1080p, don't waste bandwidth on a downgrade

---

## Step 1 — Search Using media_search.py

Run the shared search script:

```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py search \
  --type movie \
  --query "Movie Name YEAR" \
  --limit 20
```

For JSON output (programmatic use):
```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py search \
  --type movie \
  --query "Movie Name YEAR" \
  --limit 20 \
  --json
```

**Query tips:**
- Include year for precision: `"Inception 2010"` not just `"Inception"`
- Remove special characters from movie names
- If no results, broaden query (remove year, use shorter name)

### How the script works internally

1. **BitSearch.to** — Fetches HTML from `https://bitsearch.to/search?q=<QUERY>`, parses torrent cards via `/download/torrent/HASH?title=NAME` pattern, extracts metadata (size, seeders, leechers, date) from surrounding HTML, builds magnet links from info hashes.

2. **YTS.ag** — Queries `https://yts.ag/api/v2/list_movies.json?query_term=<QUERY>`. Returns verified YTS releases with quality variants (720p/1080p/2160p). Magnets constructed from torrent hashes.

3. **apibay.org** — Queries `https://apibay.org/q.php?q=<QUERY>&cat=0`. Category 0 (all) because TPB category IDs are unreliable (movies often appear in cat 207, 210, 211 instead of 201). Referer header `https://thepiratebay.org/` required.

Results are merged, deduplicated by info hash, filtered for movie-type content (excludes TV episodes, games, software), and sorted by seeders.

---

## Step 2 — Present Options to Xan

The script outputs formatted results. Present them clearly:

```
🎬 <Movie Name> — Search Results
Sources: 3/3 active | 15 results

  1. 🟢 Inception (2010) 1080p BrRip x264 - 1.85GB - YIFY
     1080p | BluRay | x264 | 1.85 GiB | S:683 L:110 | [apibay.org]

  2. 🟠 Inception.2010.1080p.BluRay.DDP5.1.x265.10bit-GalaxyRG265[TGx]
     1080p | BluRay | x265/HEVC | 2.87 GB | S:399 L:285 | [BitSearch.to] | GalaxyRG265

  3. 🟢 Inception 2010 PROPER Bluray 2160p AV1 HDR10 EN/ITA/FR/ES/DE OPUS 5.1-UH
     4K | BluRay | AV1 | 8.91 GiB | S:193 L:124 | [apibay.org]
```

**Key rules:**
- Show at least top 8-10 results
- Trust indicators: 🟢 Trusted/Verified, 🟡 Known, 🟠 Acceptable/Low, 🔴 Risky
- Flag any 🔴 entries with a warning
- If YTS 1080p exists, include as reliable baseline
- Note file extension when determinable (.mkv vs .mp4)

After presenting, **ask Xan which option (#) to download**, or offer to auto-select best (highest trust + good resolution + reasonable size).

---

## Step 3 — Download via qBittorrent

### qBittorrent Configuration

**Installation path:** `C:\\Program Files\\qBittorrent\\qBittorrent.exe`
**Web UI port:** **8080**
**Credentials:** `$QBITTORRENT_USERNAME` / `$QBITTORRENT_PASSWORD` (or local qBittorrent config; never hardcode credentials in skills)
**API base URL:** `http://localhost:8080/api/v2`

#### ⚠️ WSL CRITICAL: Use PowerShell Bridge

**From WSL, `curl` (and even `curl.exe`) CANNOT authenticate to qBittorrent.** The CSRF protection rejects cross-origin requests from the WSL network namespace. The ONLY working approach from WSL is the PowerShell bridge.

#### 🔄 RECOMMENDED: Auto-Watch Workflow (Batch Completion Detection)

**Use `add_and_watch.py` instead of direct `media_search.py add`** for automatic batch watching:

```bash
python3 /home/xantastique/.hermes/scripts/add_and_watch.py \
  --type movie \
  --magnet "magnet:?xt=urn:btih:HASH1..." \
  --magnet "magnet:?xt=urn:btih:HASH2..." \
  --path "D:\\Movies\\Movie Title (Year)\\"
```

**What it does:**
- Adds all magnets to qBittorrent
- Spawns a background watcher process for the entire batch
- Watcher polls every 5 minutes for completion
- When ALL torrents in batch are 100%:
  - Scans files for malware (extension + size heuristics)
  - Triggers Plex library refresh
  - Exits automatically (no polling forever)

**Advantages:**
- Event-driven: only runs when downloads are added
- Batch-aware: waits for entire batch, not just first file
- Self-cleaning: exits after completion, no stale processes
- Single Plex refresh per batch (not per file)

#### Disposable Low-Quality Test Downloads

When Xan asks to test movie downloading/cleanup rather than keep the movie, use a disposable test workflow: choose the smallest safe healthy candidate, download into the final `D:\Movies\Title (Year)\` folder shape, verify completion/media presence, then delete the torrent with `deleteFiles=true` and remove the empty test folder. Prefer a healthy 720p candidate over suspicious/dead 480p results. See `references/2026-05-27-disposable-movie-download-test.md`.

#### Manual Add (No Auto-Watch)

**Direct `add` command (no automatic watching):**

```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py add \
  --type movie \
  --magnet "magnet:?xt=urn:btih:HASH..." \
  --path "D:\\Movies\\Movie Title (Year)\\"
```

**Manual PowerShell bridge (fallback):**

```bash
powershell.exe -Command "
  \$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
  \$r = Invoke-WebRequest -Uri 'http://localhost:8080/api/v2/auth/login' \
    -Method POST -Body 'username=$QBITTORRENT_USERNAME&password=$QBITTORRENT_PASSWORD' \
    -UseBasicParsing -SessionVariable session

  \$body = @{urls='MAGNET_LINK_HERE'; savepath='D:\\Movies\\'}
  \$r2 = Invoke-WebRequest -Uri 'http://localhost:8080/api/v2/torrents/add' \
    -Method POST -Body \$body -WebSession \$session -UseBasicParsing
  Write-Output \$r2.Content
"
```

---

## Download Status

When Xan asks about download status or if a download is done:

```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py status
python3 /home/xantastique/.hermes/skills/media/media_search.py status --filter "2012"
```

Returns progress %, speed, ETA, seeds/peers for each torrent in qBittorrent.

**Prerequisite:** qBittorrent Web UI must be running. If it fails with "not accessible", start qBittorrent:
```bash
"C:\\Program Files\\qBittorrent\\qBittorrent.exe" &
```

### Batch Watcher Status

If using the auto-watch workflow (`add_and_watch.py`), watchers run in background. List active watchers:

```bash
python3 /home/xantastique/.hermes/scripts/manage_watchers.py list
```

Kill a stuck watcher:
```bash
python3 /home/xantastique/.hermes/scripts/manage_watchers.py kill <batch_id>
```

View watcher logs:
```bash
python3 /home/xantastique/.hermes/scripts/manage_watchers.py logs <batch_id>
```

Clean up dead watchers (processes that crashed):
```bash
python3 /home/xantastique/.hermes/scripts/manage_watchers.py cleanup
```

Watchers automatically exit after batch completion, so active list should be empty most of the time.

---

## Malware Scan

After a download completes, scan the target directory:

```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py scan --path /mnt/d/Movies/
python3 /home/xantastique/.hermes/skills/media/media_search.py scan --path /mnt/d/Movies/MovieName/
```

Three-layer scan:
1. **Extension check** — flags .exe, .bat, .dll, .ps1, .scr, .iso, etc. as HIGH severity
2. **Metadata check** — detects embedded PE executables in media files (CRITICAL), suspiciously small media files (MEDIUM)
3. **Windows Defender** — runs `Start-MpScan` on the directory via PowerShell

Verdict: SAFE (no critical/high issues) or ISSUES FOUND with severity breakdown.

---

## Post-Download Automation — Smart Movie Flatten + Review Queue + Plex Refresh

Reference: `references/2026-05-28-movie-smart-flatten-review-queue.md` captures the session-tested movie flattener architecture, review queue semantics, locked-file fallback, and disposable collision fixture.

The shared qBittorrent completion architecture now handles **movies and shows** through `C:\Users\santi\Documents\Hermes\Scripts\qbittorrent-batch-lib.ps1` plus `qbittorrent-on-finished.ps1`.

### Movie-specific behavior

For completed movie torrents under `D:\Movies\<Movie Title (Year)>\`:

1. **Resolve movie root** — uses qBittorrent content/save path and refuses to operate on bare `D:\Movies`.
2. **Flatten wrappers** — moves/copies video files from nested torrent wrapper folders into the movie root. Target shape:
   ```text
   D:\Movies\Movie Title (Year)\Movie.File.mkv
   D:\Movies\Movie Title (Year)\Movie.File.srt
   ```
   not:
   ```text
   D:\Movies\Movie Title (Year)\Torrent.Release.Wrapper\Movie.File.mkv
   ```
3. **Sidecars** — moves subtitle/metadata sidecars matching movie base names alongside the movie file.
4. **Duplicate handling** — exact same-size/same-hash duplicates are removed from the wrapper.
5. **Conflict handling** — if an incoming/new movie differs from the existing local movie at the target path, the default is `remote`:
   - keep the newly downloaded movie in the Plex library
   - move the old/local movie into `D:\Review\YYYY-MM-DD\HH-MM-SS\`
   - expose it under `D:\Review\current\`
   - update `D:\Review\current\review.yaml`
6. **Manual review TUI** — run `C:\Users\santi\Desktop\smart_org.bat`:
   - `remote` / Enter: keep newly downloaded media [default]
   - `local`: restore old/local media over the new file
   - `merge`: keep both in the movie folder as `new - <filename>` and `old - <filename>`
7. **Plex refresh** — movie changes refresh Plex Movies section 1.

`C:\Users\santi\Desktop\WILSON_Hash_Verify.bat` is a legacy alias for the same smart organizer; it is no longer hash-only.

The movie flattener uses `Move-Item`, then falls back to `Copy-Item` if Windows/qBittorrent/Plex still holds a read handle. If source cleanup is locked, it logs `MOVIE SOURCE REMOVE DEFERRED` and leaves the source wrapper for a later pass instead of lying about success.

---

## Plex Library Scans

When a movie is already downloaded but not appearing in Plex UI, trigger a library refresh.

**⚠️ WSL Note:** From WSL, `localhost:32400` is unreachable. Use `192.168.128.1:32400` (Windows host IP) instead. Also, PUT with header auth returns 404 — use GET with `X-Plex-Token` as a query parameter.

**Using the Plex Refresh Script (RECOMMENDED):**

```bash
# List all sections; default is safe/no-refresh
python3 /home/xantastique/.hermes/skills/media/get-movie/scripts/plex_refresh.py
python3 /home/xantastique/.hermes/skills/media/get-movie/scripts/plex_refresh.py --list

# Refresh specific section by exact name when possible
python3 /home/xantastique/.hermes/skills/media/get-movie/scripts/plex_refresh.py --section "Movies"
python3 /home/xantastique/.hermes/skills/media/get-movie/scripts/plex_refresh.py --section "Shows"
python3 /home/xantastique/.hermes/skills/media/get-movie/scripts/plex_refresh.py --section "More Shows"

# Refresh all libraries only when explicitly needed; full scans can stress Plex
python3 /home/xantastique/.hermes/skills/media/get-movie/scripts/plex_refresh.py --all --delay 3
```

**Setup (one-time):**
```bash
# Extract token from Plex UI (F12 → Network tab → X-Plex-Token header)
# Add to ~/.hermes/.env
echo "PLEX_TOKEN=your-token-here" >> ~/.hermes/.env

# Verify setup
python3 /home/xantastique/.hermes/skills/media/get-movie/scripts/plex_refresh.py --list
```

**Manual Scan via curl (fallback from WSL):**
```bash
# Must use Windows host IP + token as query param (not header)
TOKEN=$(cat /home/xantastique/.hermes/plex_token.txt)
curl -s -o /dev/null -w "%{http_code}" \
  "http://192.168.128.1:32400/library/sections/1/refresh?X-Plex-Token=$TOKEN"
# 200 = success
```

**Manual Scan (Windows browser):**
- Open `http://localhost:32400/web`
- Settings → Manage → Scan Library Files

**Important:**
- Plex tokens are stable — extract once and reuse. They do not rotate automatically.
- From WSL: always use `192.168.128.1:32400`, not `localhost:32400`
- From WSL: use GET with `?X-Plex-Token=TOKEN` query param, not PUT with header
- Refresh is async — items appear in UI after Plex processes them.
- **WSL automation**: When running from WSL, Windows `localhost` is inaccessible. Use `plex_scan.py` helper at `/home/xantastique/.hermes/scripts/plex_scan.py` with the Windows host IP (typically `192.168.128.1`). See `references/plex-wsl-automation.md` for full setup pattern.

---

## Gap Analysis — Franchise & Sequel Detection

**Detect missing sequels, prequels, and franchise entries for any movie.**

For broader "what up-to-date movies am I missing / what should I add" requests, do a recommendation audit instead of pure franchise gap analysis:

1. Scan `D:\\Movies` first and normalize local titles before any network lookup.
2. Use metadata/indexer APIs for availability and quality signals, not as the sole taste/ranking source.
3. Keep raw feed output separate from the final recommendation shortlist if the feed is polluted, future-looking, or availability-biased.
4. Present a curated practical shortlist, then lower-priority/completionist titles separately.

See `references/2026-05-27-recent-movie-recommendation-audit.md` for the session-tested pattern.

```bash
# Check what franchise entries you're missing
python3 /home/xantastique/.hermes/skills/media/media_search.py gap \
  --type movie --query "Insidious"

# Also search for missing entries on indexers
python3 /home/xantastique/.hermes/skills/media/media_search.py gap \
  --type movie --query "John Wick" --search-missing

# JSON output for programmatic use
python3 /home/xantastique/.hermes/skills/media/media_search.py gap \
  --type movie --query "The Matrix" --json

# Override default library path
python3 /home/xantastique/.hermes/skills/media/media_search.py gap \
  --type movie --query "Alien" --library "/mnt/d/Movies/"
```

**Output example:**
```
🎬 Insidious — Franchise/Sequel Gap Analysis [IMDB (Cinemagoer)]
Entries: 1/6 (16.7%)

===== MISSING ENTRIES =====
  ❌ Insidious 2 — possible sequel
  ❌ Insidious 3 — possible sequel
  ❌ Insidious 4 — possible sequel
  ❌ Insidious 5 — possible sequel

===== EXISTING ENTRIES =====
  ✅ Insidious — original
```

**With `--search-missing`**, searches for each missing franchise entry on indexers.

**Data source:** Cinemagoer (IMDB database) for verified sequel/prequel relationships. Falls back to title-based heuristic detection (numbered sequels) and TVmaze franchise search. Scans `D:\\Movies\\` for matching filenames.

⚠️ **Gap analysis false positives:** Heuristic detection can misidentify numbered repacks/reuploads as sequels. Example: "Before Sunset" query returned "Before Sunset 2-6" as missing entries (false positives). For known trilogies/franchises with clear titles, prefer direct `search` command instead. See `references/tool-quirks-wsl-windows-env.md` for full details.

### When to use gap analysis

- Xan asks "are there sequels to [movie] I'm missing"
- Xan asks "do I have all the [franchise] movies"
- Xan asks to complete a franchise/collection
- Before downloading, to see what's already there

---

## Complete Workflow

```
0. Receive movie name from Xan
1. LIBRARY PRE-CHECK: Scan D:\Movies\ for existing copy
1a. If movie exists: run GAP ANALYSIS to detect missing sequels/franchise entries
2. Run: python3 media_search.py search --type movie --query "Movie Name YEAR" --limit 20
   OR: python3 media_search.py gap --type movie --query "Movie Name" --search-missing
3. Present formatted results with trust indicators
4. Wait for Xan's selection
5. Get magnet link(s) from selected result(s)
6. Ensure qBittorrent running (start if needed)
7. Submit magnet(s) with D:\Movies\ as destination via add_and_watch.py
8. Report: "Added to qBittorrent — batch watcher started"
9. Watcher runs in background:
   - Polls qBittorrent every 5 minutes
   - Checks if ALL torrents in batch are complete
   - When complete: scans files, refreshes Plex, exits
10. When watcher/hook completes, verify:
   - no root-level torrent wrapper folder contains movie video files
   - movie media lives directly under `D:\Movies\Movie Title (Year)\`
   - `D:\Review\current\review.yaml` contains any unresolved conflicts
   - malware scan is SAFE or issues are reported
   - Plex Movies section refreshed
11. If conflicts remain, run `C:\Users\santi\Desktop\smart_org.bat` and choose `remote`, `local`, or `merge` in the TUI
```

---

## Code Architecture

The search system uses a modular OOP design under `lib/`:

```
lib/
├── search/          # Indexer implementations (BaseSearcher ABC)
│   ├── bitsearch.py # BitSearchSearcher
│   ├── yts.py       # YTSSearcher
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

To add a new indexer: create a class inheriting from `BaseSearcher`, implement `search()` and `source_name`, register it in `SearchEngine.__init__`.

---

## Known Issues & Pitfalls

1. **YTS.mx is dead.** DNS returns NXDOMAIN. Use `YTS.ag` instead (requires `-L` for redirect). The script handles this automatically.

2. **EZTV API search is broken.** The search/query parameters are ignored — it always returns the latest global uploads regardless. Only `imdb_id` works but requires knowing the IMDB ID first. Not worth the complexity; BitSearch covers TV results better.

3. **1337x is Cloudflare-blocked.** All requests hit "Just a moment..." challenge. Cannot scrape without a browser/headless solution.

4. **apibay category IDs are unreliable.** Movies appear in cat 201, 207, 210, 211, 199, etc. Always use `cat=0` and filter results by content pattern instead.

5. **BitSearch.to magnet links are HTML-entity encoded.** `&#x3D;` instead of `=`. The script handles decoding via `html.unescape()`.

6. **Magnet links need URL-encoding for curl.** Use `--data-urlencode`.

7. **Fake/malicious torrents.** Never auto-download without showing options. Trust classification blocks exe/iso/keygen patterns.

8. **Game results mixed in.** The script filters these out automatically (FitGirl, CODEX, RUNE, etc.) when `--type movie` is used.

9. **qBittorrent API from WSL requires PowerShell bridge.** `curl` and `curl.exe` both fail with 401 Unauthorized due to CSRF protection. Only `powershell.exe -Command "Invoke-WebRequest ..."` works because it runs natively on Windows and is treated as same-origin. See `references/qbittorrent-api-wsl-setup.md`.

10. **Plex API from WSL requires Windows host IP.** `localhost:32400` is unreachable from WSL. Use `192.168.128.1:32400`. Also, PUT with header auth returns 404 — use GET with `?X-Plex-Token=TOKEN` as query param instead.

11. **Do not default to full-library Plex refreshes.** Full scans can stress or wedge Plex on large libraries. The refresh helper now lists sections by default and requires `--section`, `--section-id`, or explicit `--all`. Section-name matching prefers exact matches first so `Shows` does not accidentally target `More Shows`. Use `--delay` for multi-section runs.

12. **Gap analysis heuristic false positives.** Numbered sequel detection can misidentify repack/reupload torrents as actual sequels. Example: "Before Sunset" query detected "Before Sunset 2-6" as missing (false positives). For known titles, prefer direct `search`. See `references/tool-quirks-wsl-windows-env.md` for more environment-specific patterns and workarounds.

13. **WSL tooling gaps.** Common Linux tools like `jq` and `file` are not installed. Prefer Python `json` module for parsing and `ls -lh` + extension checks for file verification. Windows Defender scan via PowerShell can timeout (60s); for trusted sources, accept lighter verification or run async.

14. **Batch watcher timeout.** Watchers exit after 24 hours if torrents don't complete (stuck at 0%, missing metadata, dead swarm). Check qBittorrent status manually and re-add if needed.

15. **Raw movie availability feeds are not recommendation engines.** YTS/indexer popularity pulls can return polluted, future-looking, concert/special, or low-relevance entries. Use them to verify availability/quality after a title is selected or curated; do not blindly present the raw ranking as "recommended movies." Keep raw feed artifacts clearly labeled and present a curated shortlist filtered against `D:\\Movies`.

16. **Do not trust future-looking or polluted availability results.** If an indexer reports a not-yet-released or implausibly dated movie with high seed counts, treat it as suspect until the title/year/source are cross-checked. Prefer exact title + year + known release family; do not let seed count override identity.

17. **Batch movie acquisition precheck includes normalized duplicates.** Before adding a list of requested movies, scan `D:\\Movies` for exact title/year folders and normalized near-duplicates. Malformed folder names can hide existing copies; report duplicate suspects and do not delete or replace without hash/quality comparison.

---

## Trust Level Classification

| Trust | Indicator | Score |
|---|---|---|
| **🟢 TRUSTED** | VIP/Moderator uploader, or known safe release group (YTS, GalaxyRG, BONE, SPARKS, Framestor, etc.) | ★★★★★ |
| **🟡 KNOWN** | Trusted/Helper skull | ★★★★☆ |
| **🟢 VERIFIED** | No badge but excellent swarm health (>50 seeders, >5:1 ratio) | ★★★☆☆ |
| **🟠 ACCEPTABLE** | No badge, moderate seeders (>10) | ★★☆☆☆ |
| **🟠 LOW** | Few seeders (1-10) | ★☆☆☆☆ |
| **🔴 RISKY** | 0 seeders, spam signals, suspicious name patterns | ☆☆☆☆☆ |

**Auto-flag as suspicious:**
- Name contains `exe`, `iso`, `installer`, `keygen`, `serial`, `free download`
- Size suspiciously small for claimed resolution (<700 MiB for 1080p, <2 GiB for 4K)
- Seeder count 0 or impossibly high with 0 leechers

---

## Verification Checklist

- [ ] Library pre-check executed — scanned D:\Movies\ for existing copy
- [ ] Search executed via media_search.py (3 sources queried)
- [ ] Results filtered for movie-type content (no TV/games)
- [ ] Options presented with trust indicators and source tags
- [ ] Xan confirmed selection
- [ ] Magnet link(s) obtained from result(s)
- [ ] qBittorrent running and Web UI accessible
- Agent-added movie torrents must pass `--type movie`; `media_search.py add` writes qBittorrent category `movie`, and the qBittorrent hooks use that category/path root so movie downloads never enter the Shows batch flattener.
- [ ] Batch watcher or qBittorrent hook completed
- [ ] Movie wrapper folders flattened so media files live directly under `D:\Movies\Movie Title (Year)\`
- [ ] Hash-different movie conflicts queued in `D:\Review\current\review.yaml` with `remote` as default
- [ ] Plex Movies section refreshed