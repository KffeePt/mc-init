---
name: get-music
description: "Use when Xan asks to download, find, search for, or get music — albums, discographies, singles, or OSTs. Searches multiple public media indexers, presents options with audio quality metadata and trust levels, and downloads via qBittorrent."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [music, download, media-index, qbittorrent, media, album, flac]
    related_skills: [get-movie, get-show, media-transcoding-ffmpeg]
---

# Get Music — Multi-Source Music Search & Download

## Overview

Searches **multiple public media indexers** for music, classifies results into **Albums/Discographies** vs **Singles/Tracks**, presents options with audio quality metadata (FLAC, 320kbps, Hi-Res, etc.) and trust levels, then downloads via qBittorrent to `D:\\Music\\` on **BIGGIE**.

**Sources (in priority order):**
1. **BitSearch.to** — Primary. HTML-based, no Cloudflare, reliable, good metadata.
2. **apibay.org** — Fallback. Pirate Bay API. Category filtering unreliable (use `cat=0`).

**Shared search library:** `/home/xantastique/.hermes/skills/media/lib/` (modular OOP)

**Drive mapping:**
- **BIGGIE** → `D:\\Movies\\` (movies) + `D:\\Music\\` (music)
- **MAMBA** → `F:\\Shows\\` (TV shows)

**Sort preference for music:** FLAC > Hi-Res > 24-bit > 320kbps > 256kbps > 192kbps > MP3. Among same quality: lowest size, then seeders.

**Note:** YTS is movie-only. EZTV API is broken. Only BitSearch and apibay are used for music.

## When to Use

- Xan asks to download or find music, an album, a discography, a single, or an OST
- Xan says "get me [artist] album" / "download [album] FLAC" / "find [song]"
- Any request implying music acquisition

**Don't use for:** Movies → `get-movie`, TV shows → `get-show`

---

## Step 0 — Library Pre-Check (MANDATORY)

**Before searching anything, always check if Xan already has the music.**

```python
import os

MUSIC_DIR = "/mnt/d/Music/"
query_name = "artist or album name here"  # lowercase, simplified

if os.path.exists(MUSIC_DIR):
    existing = []
    for entry in os.listdir(MUSIC_DIR):
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
- If Xan already has FLAC, don't waste bandwidth on an MP3 download

---

## Step 1 — Search Using media_search.py

Run the shared search script with `--type music`:

```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py search \
  --type music \
  --query "Artist Album FLAC" \
  --limit 25
```

For JSON output (programmatic use):
```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py search \
  --type music \
  --query "Artist Album FLAC" \
  --limit 25 \
  --json
```

**Query tips:**
- Include format for precision: `"Radiohead OK Computer FLAC"` not just `"OK Computer"`
- For discographies: `"Artist Discography FLAC"`
- For specific albums: `"Artist Album YEAR FLAC"`
- If no results, broaden query (remove format, use just artist name)
- For individual tracks: `"Artist Song Title 320"`

### How music filtering works

Results are filtered to only include entries matching music patterns:
- Quality tags: FLAC, MP3, AAC, ALAC, 320kbps, V0, Hi-Res, 24bit, Lossless
- Content types: Album, Discography, OST, Soundtrack, Vinyl, LP, EP, Single, Deluxe, Remaster
- CUE/LOG/SCANS indicators (common in music release packaging)
- Audio file extensions in name: .mp3, .flac, .m4a, etc.

Game results (FitGirl, CODEX, RUNE, Repack, etc.) and TV patterns are automatically excluded.

---

## Step 2 — Classify: Albums vs Singles

**Classify results into two types before presenting:**

### Type A: Album / Discography

A torrent containing a full album, multiple albums, or discography.

**Detection patterns** (match ANY):
```regex
(?i)(album|discography|discog|complete\s+collection|vinyl|lp|ep|deluxe|remaster|ost|soundtrack|score|b-sides|live\s+(album|concert))
```

**Sub-classify by scope:**

| Scope | Pattern | Example |
|---|---|---|
| **Single Album** | `Album` alone or year tag | "Radiohead - OK Computer FLAC" |
| **Deluxe/Remaster** | `Deluxe`, `Remaster` | "OK Computer OKNOTOK Deluxe FLAC" |
| **Discography** | `Discography`, `Discog` | "Radiohead Discography FLAC" |
| **OST/Score** | `OST`, `Soundtrack`, `Score` | "Interstellar OST FLAC" |

### Type B: Single/Track

A single song or a few tracks.

**Detection patterns:**
```regex
(?i)(single|track|song|(19|20)\d{2}\s*-\s*\d{2}\s)
```

---

## Step 3 — Present Options to Xan

**Always present BOTH categories separately. Albums first, then singles.**

```
🎵 <Artist - Album> — Search Results
Sources: 2/2 active | 15 results

===== ALBUMS / DISCOGRAPHIES =====

 1. 🟢 Radiohead - OK Computer OKNOTOK [Hi-Res] FLAC 24BIT 96kHz
    Hi-Res | 1.96 GB | S:25 L:3 | [BitSearch.to] | EICHBAUM

 2. 🟠 Radiohead - OK Computer [FLAC-1997]
    FLAC | 360 MiB | S:2 L:1 | [BitSearch.to]

 3. 🟠 Radiohead - OK Computer (2001) [MP3 320]
    320kbps | 125 MiB | S:15 L:4 | [apibay.org]

===== SINGLES / TRACKS =====

 4. 🟠 Radiohead - Paranoid Android (1997) [FLAC]
    FLAC | 42 MiB | S:5 L:1 | [BitSearch.to]
```

**Key presentation rules:**
- **Albums ALWAYS shown first** — they're usually the better value
- Within each section: sort by **Quality desc → Trust desc → Seeders desc**
- Show **at least top 5 albums + top 5 singles**
- Note audio quality (FLAC, 320, Hi-Res) prominently
- Flag any 🔴 entries with a warning
- For discographies, note total size if available

---

## Step 4 — Download via qBittorrent

### Destination Directory

**Music goes to `D:\\Music\\<Artist>\\<Album>\\` on BIGGIE.**

### qBittorrent Web UI Connection

**Configuration:**
- **Path:** `C:\\Program Files\\qBittorrent\\qBittorrent.exe`
- **Web UI port:** 8080
- **Credentials:** `$QBITTORRENT_USERNAME` / `$QBITTORRENT_PASSWORD` (or local qBittorrent config; never hardcode credentials in skills)
- **API base:** `http://localhost:8080/api/v2`

#### ⚠️ WSL CRITICAL: Use PowerShell Bridge

**From WSL, `curl` (and even `curl.exe`) CANNOT authenticate to qBittorrent.** The CSRF protection rejects cross-origin requests from the WSL network namespace. The ONLY working approach from WSL is the PowerShell bridge:

```bash
powershell.exe -Command "
  \$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
  \$r = Invoke-WebRequest -Uri 'http://localhost:8080/api/v2/auth/login' \
    -Method POST -Body 'username=$QBITTORRENT_USERNAME&password=$QBITTORRENT_PASSWORD' \
    -UseBasicParsing -SessionVariable session

  # Add torrent
  \$body = @{urls='MAGNET_LINK_HERE'; savepath='D:\\Music\\<Artist>\\<Album>\\'}
  \$r2 = Invoke-WebRequest -Uri 'http://localhost:8080/api/v2/torrents/add' \
    -Method POST -Body \$body -WebSession \$session -UseBasicParsing
  Write-Output \$r2.Content
"
```

Or use the library's `add` command:
```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py add \
  --magnet "magnet:?xt=urn:btih:HASH..." \
  --path "D:\\Music\\Radiohead\\OK Computer\\"
```

### Download Scenarios

#### Scenario A: Single Album
Add one torrent, set path to `D:\\Music\\<Artist>\\<Album>\\`. Done.

#### Scenario B: Discography (Multiple Albums)
```bash
for album_name, magnet in albums_to_download:
    add_to_qbittorrent(magnet, "D:\\Music\\<Artist>\\")
    sleep 1  # Rate-limit
```

#### Scenario C: Individual Tracks
1. Add each track to `D:\\Music\\<Artist>\\Singles\\`
2. Rate-limit between submissions

---

## Download Status

When Xan asks about download status or if a download is done:

```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py status
python3 /home/xantastique/.hermes/skills/media/media_search.py status --filter "Radiohead"
```

Returns progress %, speed, ETA, seeds/peers for each torrent in qBittorrent.

**Prerequisite:** qBittorrent Web UI must be running. If it fails with "not accessible", start qBittorrent:
```bash
"C:\\Program Files\\qBittorrent\\qBittorrent.exe" &
```

---

## Malware Scan

After a download completes, scan the target directory:

```bash
python3 /home/xantastique/.hermes/skills/media/media_search.py scan --path /mnt/d/Music/
python3 /home/xantastique/.hermes/skills/media/media_search.py scan --path /mnt/d/Music/Radiohead/
```

Three-layer scan:
1. **Extension check** — flags .exe, .bat, .dll, .ps1, .scr, .iso, etc. as HIGH severity
2. **Metadata check** — detects embedded PE executables in media files (CRITICAL), suspiciously small media files (MEDIUM)
3. **Windows Defender** — runs `Start-MpScan` on the directory via PowerShell

Verdict: SAFE (no critical/high issues) or ISSUES FOUND with severity breakdown.

---

## Plex Library Scans

When music is downloaded but not appearing in Plex UI, trigger a library refresh.

**Using the Plex Refresh Script (RECOMMENDED):**

```bash
# Refresh all libraries
python3 /home/xantastique/.hermes/skills/media/get-movie/scripts/plex_refresh.py

# Refresh specific section by name
python3 /home/xantastique/.hermes/skills/media/get-movie/scripts/plex_refresh.py --section "Music"

# List all sections (no refresh)
python3 /home/xantastique/.hermes/skills/media/get-movie/scripts/plex_refresh.py --list
```

**Important:**
- From WSL: always use `192.168.128.1:32400`, not `localhost:32400`
- From WSL: use GET with `?X-Plex-Token=TOKEN` query param, not PUT with header
- Refresh is async — items appear in UI after Plex processes them

---

## Gap Analysis — Missing Albums & Discography Status

**Analyze what albums you have vs what's missing for any artist.**

```bash
# Check what albums are missing for an artist
python3 /home/xantastique/.hermes/skills/media/media_search.py gap \
  --type music --query "Radiohead"

# Also search for missing albums on indexers
python3 /home/xantastique/.hermes/skills/media/media_search.py gap \
  --type music --query "Gorillaz" --search-missing

# JSON output for programmatic use
python3 /home/xantastique/.hermes/skills/media/media_search.py gap \
  --type music --query "Daft Punk" --json

# Override default library path
python3 /home/xantastique/.hermes/skills/media/media_search.py gap \
  --type music --query "Pink Floyd" --library "/mnt/d/Music/"
```

**Output example:**
```
🎵 Radiohead — Discography Gap Analysis [MusicBrainz]
Albums: 0/12 (0.0%)

===== MISSING ALBUMS =====
  ❌ [1993] Pablo Honey — Album
  ❌ [1997] OK Computer — Album
  ❌ [2000] Kid A — Album
  ...

===== EXISTING ALBUMS =====
  ✅ [2007] In Rainbows
```

**With `--search-missing`**, searches for each missing album + a full discography bundle.

**Data source:** MusicBrainz (free, no API key). Only studio albums shown — compilations, live, remix, and DJ-mix albums are filtered out. Scans `D:\Music\<Artist>\` subdirectories.

### When to use gap analysis

- Xan asks "what albums am I missing from [artist]"
- Xan asks "do I have the complete discography"
- Xan asks to fill gaps in their music collection
- Before downloading, to see what's already there

---

## Complete Workflow

```
0. Receive music request from Xan (artist, album, song, discography)
1. LIBRARY PRE-CHECK: Scan D:\Music\ for existing copy
1a. If artist exists: run GAP ANALYSIS to identify missing albums
2. Run: python3 media_search.py search --type music --query "Artist Album FLAC" --limit 25
   OR: python3 media_search.py gap --type music --query "Artist" --search-missing
3. CLASSIFY each result → album/discography OR single/track
4. Present options in TWO SECTIONS: ALBUMS, then SINGLES
5. Wait for Xan's selection(s)
6. Get magnet link from selected result
7. Ensure qBittorrent running (start if needed)
8. Submit magnet with D:\Music\<Artist>\<Album>\ as destination via PowerShell bridge
9. Verify addition via PowerShell torrents/info
10. Report: "Added to qBittorrent — <Name> [<Size>] → D:\Music\<Artist>\"
11. When download completes: scan --path /mnt/d/Music/<Artist>/ for malware
12. Report scan verdict (SAFE / issues found)
13. Trigger Plex library refresh if needed
```

---

## Code Architecture

The search system uses a modular OOP design under `lib/`:

```
lib/
├── search/          # Indexer implementations
│   ├── base.py      # BaseSearcher ABC
│   ├── bitsearch.py # BitSearchSearcher
│   ├── yts.py       # YTSSearcher (movies only)
│   ├── apibay.py    # ApiBaySearcher
│   └── engine.py    # SearchEngine (orchestrator)
├── filters/         # Media type classifiers
│   ├── base.py      # BaseFilter ABC
│   ├── movie.py     # MovieFilter
│   ├── show.py      # ShowFilter
│   └── music.py     # MusicFilter
├── metadata/        # Metadata extraction
│   ├── extractors.py # Resolution, format, codec, audio quality, release group
│   └── trust.py     # TrustClassifier
├── gap/             # Gap analysis (BaseGapAnalyzer ABC)
│   ├── base.py      # GapResult, BaseGapAnalyzer
│   ├── show.py      # ShowGapAnalyzer (TVmaze API)
│   ├── music.py     # MusicGapAnalyzer (MusicBrainz API)
│   └── movie.py     # MovieGapAnalyzer (Cinemagoer + heuristic)
├── qbittorrent/     # QBittorrentClient (PowerShell bridge)
├── scanner/         # MalwareScanner
└── formatters/      # ResultFormatter, StatusFormatter, ScanFormatter, GapFormatter
```

To extend: create a new class inheriting from the relevant ABC, register it, done.

---

## Known Issues & Pitfalls

1. **YTS is movie-only.** No music results from YTS. Only BitSearch + apibay for music.

2. **EZTV API is broken.** Search params ignored. Not used for music.

3. **1337x is Cloudflare-blocked.** Cannot scrape without browser automation.

4. **apibay category IDs are unreliable for music.** Music appears in cat 100, 104, etc. Always use `cat=0` and filter by content pattern.

5. **Quality naming inconsistency.** Uploaders use "FLAC", "flac", "FLAC-1997", "24bit-96kHz", "Hi-Res", etc. The audio quality extractor handles common variants.

6. **Discography size.** Full discographies can be 10-50+ GiB. Always show size prominently and warn Xan before downloading.

7. **CUE/LOG/SCANS.** Music releases often include .cue files (track listing), .log (EAC rip log), and scan folders (album art). These are legitimate — don't flag them as suspicious.

8. **MP3 vs FLAC confusion.** Some torrents are labeled "FLAC" but contain MP3. Trust classification helps but isn't foolproof. If a FLAC album is suspiciously small (<150 MiB for a full album), flag it.

9. **qBittorrent API from WSL requires PowerShell bridge.** `curl` and `curl.exe` both fail with 401 Unauthorized due to CSRF protection. Only `powershell.exe -Command "Invoke-WebRequest ..."` works.

10. **Music on BIGGIE (D:).** NOT on MAMBA (F:). Music downloads go to `D:\\Music\\`.

---

## Trust Level Classification

Same system as get-movie/get-show, with music-specific groups added:

| Trust | Indicator | Score |
|---|---|---|
| **🟢 TRUSTED** | VIP/Moderator + known groups | 5/5 |
| **🟡 KNOWN** | Trusted/Helper skull | 4/5 |
| **🟢 VERIFIED** | No badge but excellent swarm health | 3/5 |
| **🟠 ACCEPTABLE** | No badge, moderate seeders | 2/5 |
| **🔴 RISKY** | Low seeds, spam signals | 1/5 |

**Known safe music release groups** (auto-TRUSTED):
DHV, FID, DRS, MTC, Qobuz, Deezer, TIDAL, Beatport, plus all video groups (GalaxyRG, FLUX, etc.)

---

## Verification Checklist

- [ ] Library pre-check executed — scanned D:\Music\ for existing copy
- [ ] Search executed via media_search.py with --type music
- [ ] Results filtered for music-type content only
- [ ] Results classified into albums vs singles
- [ ] Both sections presented with quality metadata and trust indicators
- [ ] Xan confirmed selection(s)
- [ ] Magnet links obtained from results
- [ ] qBittorrent running and Web UI accessible
- [ ] All torrents submitted to D:\Music\<Artist>\<Album>\ via PowerShell bridge
- [ ] Success report with count, sizes, destination, quality
