---
name: storage-explorer
description: "Omni-utility for storage management at any scale — explore, map, organize, audit, compare, hash-verify, deduplicate, clean up, fix, or safely delete across drives, folders, backups, media libraries, or repositories. Adapts strategy to situation: bounded drilldowns, persistent maps, parallel hash verification, targeted time-window scans, and safe classified deletion. NOT just a comparison tool."
version: 2.2.0
author: Wilson / Hermes Agent
license: MIT
platforms: [windows, wsl, linux]
metadata:
  hermes:
    tags: [storage, disk-usage, filelight, drive-map, cleanup, sqlite, hashes, biggie, mamba, artifacts]
    related_skills: [task-artifacts-delivery, personal-server-safety-audit, file-tree-inspection]
---

## Reference Notes

- `references/2026-05-storage-explorer-init-and-buffer-lessons.md` — bounded drilldown default, visualization preferences, deletion safety, and init-package transplant rule from the Buffer & Backups cleanup session.
- `references/2026-05-storage-saving-status-and-buffer-drilldown.md` — status-report pattern for multi-pass cleanup work, Buffer & Backups classification, bounded timeout fallback, and WSL→PowerShell quoting pitfall.
- `references/2026-05-biggie-small-cleanup-and-pop-duplicate-hash.md` — stale cleanup-candidate verification, targeted PowerShell same-size/SHA-256 duplicate hashing, and broad WSL `/mnt/d` stall fallback.
- `references/2026-05-mamba-biggie-episode-comparison.md` — three-pass cross-drive media library comparison (show-level → episode-level → hash sampling), WSL I/O throttling diagnosis, and OBS recording location pattern.
- `references/2026-05-targeted-scan-and-parallelization.md` — targeted-vs-brute-force defaults, parallelization strategy with 2–7 workers, Go preference for reusable tools, and WSL launch interop tax from this session.

## Overview

This is the unified storage-analysis skill for Xan's server. It replaces the older split between `file-light-inspection` and `drive-mapper`.

Use it for two related jobs:

1. **Fast operational visibility** — answer “what is taking space?” without turning the Telegram turn into a swamp crawl.
2. **Durable drive inventory** — maintain a persistent Plex-like lazy-update map for BIGGIE/MAMBA or other large roots when repeated reporting, duplicate detection, or content hashes are needed.

Default posture: bounded, programmatic, skeptical. Large folders lie by being slow. Do not reward them with unbounded foreground recursion.

## When to Use

This skill is the entry point for ANY storage-related task on Xan's server, regardless of scale. Choose the right strategy based on the situation:

### Exploration & Mapping
- "What's in this folder/drive?"
- Filelight-style storage maps and composition charts
- Persistent drive inventories (BIGGIE, MAMBA, or any large root)
- Top folders/files/extensions/media types
- OBS/screen recording location hunts

### Organization & Cleanup
- Cleanup candidates, space-saving review lists, deletion manifests
- Review-first classification: backups, personal media, dependency bloat, caches, archives, models, datasets, generated artifacts
- Recycle bin clearing, Plex generated versions, stale downloads
- Folder reorganization with dry-run manifests

### Integrity & Verification
- Cross-drive media library comparison (show-level → episode-level → hash sampling)
- Copy verification: did files actually copy correctly?
- Corruption checks via stratified SHA-256 sampling
- Duplicate detection with hash verification

### Safe Deletion
- Classified deletion workflows: safe → review-first → protected → hash-before-delete
- Before/after measurement and verification
- Stale manifest revalidation before acting

### Fixing & Repair
- Identifying partial/broken copies
- Finding missing files across drives
- Diagnosing copy-job crashes and resuming safely

Do not use for trivial single-folder listings; use `file-tree-inspection` instead.

## Quick Location Patterns

Known patterns for common query types on Xan's server — use these to avoid broad recursive searches:

- **OBS recordings:** `D:\Videos\Obs_Recordings` (not at root, not in Buffer & Backups). One folder, all `.mp4`, typically dated 2020–2021.
- **Plex generated versions:** `D:\Movies\Plex Versions` — Plex-created optimized/original-quality copies. Safe cleanup target when originals exist in `D:\Movies`.
- **Recycle Bin:** `D:\$RECYCLE.BIN` — payload may be large (247+ GiB seen). Clear with `Remove-Item` on children only, not the root folder itself.
- **Stale backups:** `D:\Buffer & Backups\Backups\POP-backup\Downloads` — old ISOs, installers, archives. Review-first before deletion.

## Core Safety Rules

1. **Inspection is read-only.** Do not delete/move during mapping. Deletion requires explicit target list and approval, except when Xan separately commands a specific deletion target such as a recycle bin or generated cache folder.
2. **Metadata first.** Do not open file contents unless needed for hashing, classification, or verification.
3. **Hash before duplicate deletion.** Same name/size is suspicion, not proof.
4. **Protect personal/family media and backups.** Phone backups, family videos/photos, WhatsApp databases, server backups, and one-off archives are review-first unless Xan explicitly approves deletion.
5. **Use Windows-native tools for Windows drives.** On Xan's WSL setup, prefer PowerShell/robocopy/diskusage/Windows Python for `D:\`, `F:\`, and `C:\` paths. WSL `/mnt/*` recursive scans can be slow and brittle.
6. **No unbounded foreground crawls on large drives.** Start bounded. If a durable full map is needed, run it in background with progress and ETA.

## Target Discovery — Help the User Find the Target

Before any scan, help Xan narrow the scope. Do not default to whole-drive crawls. Ask questions that shrink the problem:

1. **What changed recently?**
   - Use `CreationTime` filters for copy/backup verification (`Get-ChildItem | Where-Object { $_.CreationTime -ge $start }`).
   - Narrow to a specific time window rather than scanning everything.
   - Example: "Files copied between May 25 and May 27 before 11:30 AM" instead of "hash all 5,384 episodes."

2. **What is the specific problem?**
   - Missing shows? → compare show names, not file hashes.
   - Duplicates? → group by size first, hash only same-size groups.
   - Space pressure? → top-level sizing first, drill into the largest child.
   - Copy verification? → verify only files that were recently copied, not the entire library.
   - Corruption check? → stratified random sample, not exhaustive hashing.

3. **Match the tool to the scope.**
   - Show-level comparison: seconds. Episode-level: seconds to minutes. Full hash: hours.
   - Escalate only when findings warrant it.
   - If a faster pass answers the question, stop there.

4. **Propose a scoped plan before executing.**
   - "I'll scan only the 169 missing episodes, not all 5,376."
   - "I'll hash only files with CreationTime in the last 48 hours."
   - "I'll sample 100 random files; if any mismatch, we expand."

Brute-force whole-drive scans are allowed **only on explicit user request**. The default posture is targeted, scoped, and bounded. If Xan says "hash everything" or "scan the whole drive," comply — but warn about expected duration first.

## Smart Default Strategy

When the target is large, unknown, or likely multi-TB / hundreds of thousands of files, use this sequence by default:

1. **Target discovery first** (see above). Narrow the scope before scanning.

2. **Resolve root and existing evidence**
   - Translate Windows paths to WSL only when needed.
   - Check if an existing drive-explorer DB/report/artifact covers the target.
   - If stale but useful, report it as stale evidence, not truth.

3. **Fast top-level sizing first**
   - Prefer Windows-native bounded size summaries.
   - Use `robocopy /L /E /BYTES /NFL /NDL /NJH /R:0 /W:0` per immediate child when recursive PowerShell aggregation would be slow.
   - Use per-child timeouts. If one child times out, mark it `too large / needs drilldown` and move on instead of blocking the whole report.

4. **Bounded drilldown**
   - Drill into the largest 3–10 children only.
   - For backup swamps, inspect immediate children first, then recurse only into the biggest unknown subtree.
   - For long-running scans, write progress JSON every few thousand files with files/sec, bytes seen, current path, elapsed time, and ETA if possible.

5. **Persistent map when needed**
   - Use `drive-explorer` / the local drive-mapper project when repeated reporting, lazy updates, or duplicate/hash maps are needed.
   - First pass should usually be metadata-only; content hashing is expensive and belongs in background.

6. **Classify before recommending deletion**
   - Separate `safe/generated/reproducible`, `review-first`, `protected`, and `hash-before-delete` buckets.
   - Report exact paths and projected reclaim.
   - Ask approval before deleting anything inside review/protected buckets.

## Parallelization Strategy

For heavy I/O jobs (hash verification, duplicate scanning, metadata collection on large subtrees), parallelize aggressively. Single-threaded hashing on a spinning disk is ~0.02 eps/sec from WSL — unacceptable for more than a few dozen files.

### Worker Count

- **Detect CPU cores:** `os.cpu_count()` (Python) or `$env:NUMBER_OF_PROCESSORS` (PowerShell).
- **Use 2–7 workers** depending on available cores. Cap at 7 — beyond that, spinning-disk seek contention dominates and throughput drops.
- **Rule of thumb:** `min(7, max(2, floor(cores * 0.75)))`. Leave headroom for the OS and other processes.
- On Xan's server (GTX 1070 machine, likely 4–8 cores): start with 4 workers, adjust based on observed throughput.

### Python: `concurrent.futures.ProcessPoolExecutor`

```python
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

workers = min(7, max(2, os.cpu_count() * 3 // 4))

def hash_file(args):
    path, algo = args
    # ... hashlib.sha256, read in 64KB chunks
    return (path, hash_hex)

with ProcessPoolExecutor(max_workers=workers) as ex:
    futures = {ex.submit(hash_file, (p, 'sha256')): p for p in file_list}
    for future in as_completed(futures):
        path, h = future.result()
        results[path] = h
```

Do NOT use `ThreadPoolExecutor` for CPU-bound hashing — the GIL serializes it. Use `ProcessPoolExecutor` (real parallelism) or `concurrent.futures` with `ProcessPoolExecutor`.

### PowerShell: `ForEach-Object -Parallel`

For Windows-native jobs that don't need Python:

```powershell
$files | ForEach-Object -Parallel {
    (Get-FileHash -Path $_.FullName -Algorithm SHA256).Hash
} -ThrottleLimit 4
```

`-ThrottleLimit` controls parallelism. Match to disk capacity — 4 is a safe default for spinning disk, 7 for SSD.

### Go: Preferred for Cross-Platform Scan/Hash Tools

Go's goroutines and built-in concurrency primitives make it ideal for storage tools that need to run on both Windows and Linux:

```go
// Spawn N workers, feed file paths via channel, collect results
sem := make(chan struct{}, workers)
for _, path := range files {
    sem <- struct{}{}
    go func(p string) {
        defer func() { <-sem }()
        h := sha256File(p)
        results.Store(p, h)
    }(path)
}
```

- **When to use Go:** For reusable scan/hash/compare tools that will run repeatedly on both WSL and native Windows, Go binaries avoid Python venv/dependency headaches and WSL interop tax.
- **When to use Python/PowerShell:** For one-off investigative scripts, or when the tool already exists in Python.
- If building a persistent tool for the Hermes `Scripts/` directory, prefer Go for concurrency-heavy storage work.

### Launch Discipline

- **Kill stragglers first.** Before launching a new hash/scan job, verify no prior job is still running on the same physical disk. Two concurrent disk-intensive processes thrash the read heads.
- **Detach from WSL when possible.** Use `cmd.exe /c start` or Windows Task Scheduler for long-running native Windows jobs. WSL-launched processes pay a ~26 MB/s I/O tax.
- **Write progress files.** Every N files, write `progress.json` with done/total/match/mismatch/error/rate/ETA. This lets the agent poll without blocking.
- **Desktop Launcher — last resort.** When every WSL-launched approach fails (Start-Process silent crash, background=true silent exit, UNC path issues, cmd.exe /c start still throttled), write a self-contained `.ps1` to `C:\Users\santi\Desktop\` and tell Xan to double-click it. The script must: (a) write its own log to a known path under `Hermes\Artifacts\`, (b) produce results as CSV/JSON at that same path, (c) pop a brief completion toast or Write-Host so Xan knows it finished, and (d) include a header comment with purpose and expected runtime. This bypasses all WSL interop — the script runs fully native, at full disk speed. Once Xan confirms completion, read the results artifact from WSL.

## Python/Go Script Template: Parallel Hash Verification

Save reusable hash/compare scripts under:

```text
C:\Users\santi\Documents\Hermes\Scripts\ParallelHashVerify.ps1   (PowerShell)
C:\Users\santi\Documents\Hermes\Scripts\parallel_hash_verify.py   (Python)
C:\Users\santi\Documents\Hermes\Scripts\hashcmp\main.go            (Go, preferred)
```

Each script must:
- Accept two roots (source + destination), a file list, and a worker count.
- Hash only files in the list, not recursive scan (scanning is a separate step).
- Write progress JSON at regular intervals.
- Write results CSV with source_path, dest_path, source_hash, dest_hash, match.
- Gracefully handle missing files, permission errors, and partial runs.

## WSL Interop Rule — NEVER Launch Windows File-Intensive Work From WSL

**Hard rule:** Do not launch Windows-native file scan, hash, copy, or duplicate-detection jobs from within WSL. The WSL 9p filesystem bridge throttles all `/mnt/*` reads to ~26 MB/s regardless of whether you use `powershell.exe`, `cmd.exe`, `python.exe`, or `go.exe`.

This is NOT a disk limitation. It is a WSL architectural tax. The same script running natively on Windows achieves 100–150 MB/s on spinning disk.

### What to do instead

1. **Prefer Go binaries compiled for Windows and run natively.** A Go cross-platform hash/scan tool compiled with `GOOS=windows` runs at full native speed via `cmd.exe /c start`.
2. **Use native Windows Python** at `C:\Python314\python.exe` launched via a `.bat` file double-clicked by Xan, or via Windows Task Scheduler.
3. **Use PowerShell `.ps1` scripts** launched via `schtasks /create /tn ... /tr ... /sc once /st ...` for immediate one-shot native execution.
4. **Drop the script on the Desktop** and ask Xan to run it if automated launch fails.

### What to never do

- `powershell.exe -File script.ps1` from WSL for multi-GB file reads
- `python.exe script.py` from WSL targeting `/mnt/d` or `/mnt/f`
- Any WSL-launched process that reads video files, ISOs, or archives larger than a few MB from Windows drives
- WSL `find /mnt/d -type f` for recursive scans (use native Windows tools instead)

### Clean launch pattern

```powershell
# From WSL, write the script to the Windows filesystem, then:
cmd.exe /c "schtasks /create /tn HermesHashJob /tr 'C:\Python314\python.exe C:\Users\santi\Documents\Hermes\Scripts\hash_verify.py' /sc once /st 00:00 /f && schtasks /run /tn HermesHashJob"
```

Or drop a `.bat` file and tell Xan to double-click it. Both are faster than WSL interop.

### Immediate child listing

```powershell
Get-ChildItem -LiteralPath 'D:\Buffer & Backups' -Force |
  Select-Object Name,PSIsContainer,Length,LastWriteTime
```

### Fast per-child recursive byte estimate with robocopy

Use this pattern when a full PowerShell object walk is too slow:

```powershell
$src = 'D:\Buffer & Backups\Backups\POP-backup'
$out = robocopy $src $env:TEMP /L /E /BYTES /NFL /NDL /NJH /R:0 /W:0 2>&1
$bytesLine = $out | Where-Object { $_ -match '^\s*Bytes\s*:' } | Select-Object -First 1
$bytes = if ($bytesLine -match 'Bytes\s*:\s*([0-9]+)') { [int64]$Matches[1] } else { 0 }
[pscustomobject]@{ Path=$src; Bytes=$bytes; GiB=[math]::Round($bytes/1GB,4) }
```

Run per immediate child with a timeout. A single pathological child should not stall the entire scan.

### Metadata scan with progress

For a bounded recursive scan, write:

```text
Summary.json
Top Folders.csv
Second Level Folders.csv
Largest Files.csv
Extension Breakdown.csv
Cleanup Buckets.csv
progress.json
```

Progress must include:

- status
- elapsed seconds
- files scanned
- bytes scanned
- files/sec
- current path
- ETA or why ETA is unknowable

## Drive Explorer Persistent Map

Local project:

```text
Windows -> C:\Users\santi\Documents\Source\drive-mapper
WSL     -> /mnt/c/Users/santi/Documents/Source/drive-mapper
```

Use from project root:

```bash
cd /mnt/c/Users/santi/Documents/Source/drive-mapper
export PYTHONPATH=src
```

Metadata-only scan:

```bash
drive-explorer scan /mnt/d --label BIGGIE --db data/drives.sqlite --no-content-hash --progress 10000
drive-explorer scan /mnt/f --label MAMBA --db data/drives.sqlite --no-content-hash --progress 10000
```

Content hash scan, background only:

```bash
drive-explorer scan /mnt/d --label BIGGIE --db data/drives.sqlite --hash-content --workers 4 --progress 10000
drive-explorer scan /mnt/f --label MAMBA --db data/drives.sqlite --hash-content --workers 4 --progress 10000
```

Before reporting from the DB, verify:

- requested label/root exists
- row count is plausible
- last scan timestamp or current artifact exists
- scan was not a poisoned partial with empty breakdowns/errors roughly equal to file count

If coverage is stale/incomplete, use it as a rough map and combine with bounded live drilldowns.

## Output Artifacts

Use `task-artifacts-delivery` rules. Canonical artifact root:

```text
Windows -> C:\Users\santi\Documents\Hermes\Artifacts\YYYY-MM-DD\HH-MM-SS\<Pascal Case Purpose>\
WSL     -> /mnt/c/Users/santi/Documents/Hermes/Artifacts/YYYY-MM-DD/HH-MM-SS/<Pascal Case Purpose>/
```

Recommended files:

```text
Storage Inspection.md
Summary.json
Top Folders.csv
Second Level Folders.csv
Largest Files.csv
Extension Breakdown.csv
Cleanup Buckets.csv
Deletion Candidates.csv        # dry-run only unless deletion already approved
Charts/
  PrimaryCompositionPie.png
```

Reusable helper scripts should go under:

```text
C:\Users\santi\Documents\Hermes\Scripts\<ScriptPurpose>.ps1
/mnt/c/Users/santi/Documents/Hermes/Scripts/<ScriptPurpose>.ps1
```

Each script needs a header with purpose, date, inputs, side effects, and safety notes.

## Visualization Policy

Follow Xan's durable preference:

- One primary programmatic pie/donut chart by default.
- Use pie/donut for composition, share-of-total, cleanup buckets, media-type share, and top-folder share.
- Use bar charts only for explicit comparison/ranking tasks.
- If describing relationships between values — trends, overlap, before/after movement, rate, correlation, dependency — render a programmatic graph.
- Render factual charts with deterministic code: Python/matplotlib/Pillow/SVG or PowerShell data plus Python rendering.
- Do not use NanoBanana for factual charts.
- Use NanoBanana only for requested explainer/presentation infographics.
- Collapse pie charts to top 5 slices plus `Other` when there are more than 6 slices.

## Classification Buckets

Use these labels in reports:

- **Safe/generated/reproducible:** recycle bin, generated Plex versions, package caches, dependency folders, build outputs, thumbnails/caches, generated optimized media, temporary downloads.
- **Review-first:** old backups, archives, installers, ISOs, VM images, OBS/screen recordings, old project snapshots, old server backups.
- **Protected:** family/personal photos/videos, phone camera folders, WhatsApp databases, unique documents, current server backups, media libraries unless explicitly targeted.
- **Hash-before-delete:** probable duplicates, copied archives, duplicate server backups, model files that may exist elsewhere, same-name media across backup generations.

## Deletion Workflow

1. Exact target path(s).
2. Measure before: bytes/files/dirs and free space.
3. Confirm target is within approved scope.
4. Verify the target still exists live; stale scan candidates are evidence, not authorization or current reclaim.
5. Delete.
6. Measure after: target exists?, free space delta, leftover files.
7. Record result in `STATE.md` and artifact report.

Do not infer approval for broad folders from approval of a narrow generated target.

## Duplicate Hash Workflow

Use this when Xan asks for duplicate detection, duplicate cleanup, or hash analysis on large Windows-hosted storage:

1. **Bound the scope first.** Prefer a specific subtree or persistent Windows-native background index over a whole-drive WSL crawl.
2. **Revalidate old manifests.** Check that candidate paths still exist before hashing or reporting them as current. If an old subtree is gone, call the manifest stale.
3. **Group by size before hashing.** Hash only same-size groups above a useful threshold unless Xan explicitly wants exhaustive tiny-file hashing.
4. **Use Windows-native hashing for Windows drives.** Prefer PowerShell `Get-FileHash` against `D:\`/`F:\` paths rather than WSL `/mnt/d` recursion for broad or backup-heavy scans.
5. **Report evidence, not implied cleanup.** Emit files considered, same-size groups checked, files hashed, hash errors, exact duplicate groups, keep candidate, extra candidates, and potential reclaim.
6. **Deletion is separate approval.** Exact hash duplicates inside backups/build artifacts still require explicit approval of the extra-candidate list, especially when reclaim is trivial.

If broad WSL hashing stalls or enters disk sleep, kill it and switch to targeted PowerShell hashing or a Windows-native indexed/background pass. Do not let it sit there like a cursed aquarium.

## Cross-Drive Media Library Comparison

Use when Xan asks to verify whether one media library (e.g. MAMBA `F:\Shows`) has been fully and correctly copied to another (e.g. BIGGIE Archived `D:\Archived Shows`). This is a three-pass workflow — escalate only when findings warrant it.

### Pass 1 — Show-Level (seconds)

Collect show name, episode count, total bytes per show on both sides. Compare show names. Identify shows present in both, missing from the archive, and extra on the archive side. Report which shows have zero episodes archived — a completely absent show is a bigger gap than one missing its latest season.

### Pass 2 — Episode-Level (seconds to low minutes)

Build episode maps keyed by lowercase filename. Match across sides. Compare file sizes. Report:
- Matched + size-identical episodes
- Episodes missing from the archive (present only on MAMBA)
- Episodes missing from MAMBA (present only on the archive)
- Size mismatches (same name, different size — possible re-encode)

Use PowerShell `Get-ChildItem` with recursive directory traversal, filtered to video extensions. This pass completes in seconds for thousands of episodes. It gives you the full gap analysis without touching file contents.

### Pass 3 — Hash Verification (only when needed)

Only escalate to SHA-256 when:
- Size mismatches exist and you need to determine if they're truly different
- The user explicitly demands cryptographic certainty
- Use stratified random sampling, not exhaustive hashing (see Pitfall 16 below)

For 5,000+ episodes on a single spinning disk, exhaustive dual-copy SHA-256 hashing takes ~36 hours via WSL-launched processes. A stratified sample of 200 episodes across all shows gives >99.9% confidence. If any sample mismatches appear, expand the scope.

### Output Shape

```text
Show Comparison.csv — show name, episode counts both sides, matched, missing, extras
Episode Mismatches.csv — per-episode path, size, status (missing_from_archived, size_mismatch, etc.)
Comparison Summary.json — aggregate counts, missing GiB estimate
```

Do not delete or move files during comparison. This is read-only evidence collection.

## ETA / Progress Reporting Rule

For long scans/hash passes/background jobs, always report:

- process/session ID
- running/completed/stalled/failed
- elapsed time
- files/dirs/bytes seen so far
- current rate
- ETA if denominator exists
- if ETA is unknowable, say why and give the next confidence milestone

Never say only “still running.” Useless. Almost decorative.

## Common Pitfalls

1. **Full recursive crawls in-chat.** Use bounded drilldowns first. Background if it must be full.
2. **Treating `Backups` as junk.** Backups can be waste, insurance, or evidence. Classify first.
3. **Letting one huge child block the whole scan.** Per-child timeout; mark and continue.
4. **Trusting stale DBs blindly.** Verify coverage and age.
5. **Deleting personal media because it is large.** Large is not junk. It is a suspect.
6. **Name/size duplicate deletion.** Hash first.
7. **Bar-chart reflex.** Pie/donut default; bars only for comparison/ranking.
8. **NanoBanana factual charts.** No. Deterministic charts only.
9. **WSL scanning Windows drives by habit.** Prefer Windows-native traversal for Windows filesystems.
10. **Poisoned partial outputs.** If totals are plausible but breakdowns are empty or errors dominate, rerun with a different scanner.
11. **WSL shell eating PowerShell variables.** When calling `powershell.exe` from WSL, use single-quoted outer scripts or escape `$`; otherwise Bash expands `$_` and `$name` before PowerShell sees them.
12. **Conflating reclaim tracker with exact accounting.** For multi-pass cleanups, report current live free space separately from approximate cumulative reclaimed GiB, and label overlap/uncertainty instead of pretending byte-perfect history.
13. **Acting on stale cleanup scans.** A path that was huge in a prior report may already be gone. Verify live existence and current size before claiming deletion or reclaim.
14. **Trusting old duplicate manifests.** Re-check candidate paths before hashing/deletion; if paths are absent, mark the manifest stale and pivot to current scoped analysis.
15. **Whole-drive WSL duplicate hashing on BIGGIE.** Broad `/mnt/d` hash crawls can stall badly. Prefer targeted PowerShell same-size/SHA-256 passes or Windows-native background indexing.
16. **WSL-launched Windows processes are I/O-throttled for large file hashing.** Even native Windows Python or PowerShell launched from WSL reads large video files at ~26 MB/s instead of the expected 100–150 MB/s. The WSL 9p interop layer is the bottleneck. When exhaustive two-copy hashing across drives is needed, either (a) use stratified random sampling for practical certainty without brute-forcing, or (b) launch fully detached via `cmd.exe /c start` to reduce interop overhead, or (c) run the hash job as a Windows-native background process outside WSL entirely. Do not report the 26 MB/s rate as normal — it is an interop tax and a design constraint.
17. **Multiple concurrent disk-intensive processes on the same physical drive stall each other.** When one Python process is hashing large files from D: and another is also reading from D: or F: (same physical disk, different partitions), the read heads thrash and both processes slow to a crawl. Before launching a new hash/scan job, verify no prior job is still running on the same physical disk. Kill stragglers first.
18. **Whole-drive brute-force scans are the last resort, not the default.** Start with target discovery: ask what changed recently (CreationTime windows), what the specific problem is (missing files, duplicates, corruption), and propose the lightest pass that answers the question. Whole-drive crawls or exhaustive hashing require explicit user approval.
19. **Single-threaded hashing is unacceptable for more than a few dozen files.** Use ProcessPoolExecutor (Python), ForEach-Object -Parallel (PowerShell), or goroutines (Go). Auto-scale to 2–7 workers based on CPU cores. Cap at 7 — spinning disk seek contention dominates beyond that.
21. **Never launch Windows file-intensive work from WSL.** The WSL 9p interop bridge caps all `/mnt/*` reads at ~26 MB/s. Use native Windows Python (`C:\Python314\python.exe`), Go binaries compiled for Windows, or PowerShell `.ps1` scripts launched via `schtasks` or double-click. If automated launch fails, drop the script on Xan's Desktop and ask him to run it. Do not sit there brute-forcing through interop tax like a cat pushing a door labeled PULL.
22. **WSL-launched PowerShell scripts can crash silently with no error output.** `Start-Process -WindowStyle Hidden` swallows all errors. `background=true` with `powershell.exe -File` can exit code 0 with zero output if the script hits an uncatchable error (e.g., regex on null, type mismatch in a filter block). When a script produces no log file after 2+ minutes, assume it crashed. Do not relaunch the same approach — escalate to a Desktop Launcher script (see Launch Discipline) or switch to a simpler bounded command.

## Verification Checklist

- [ ] Correct root resolved.
- [ ] Existing maps/artifacts checked when relevant.
- [ ] For large roots, bounded top-level drilldown attempted before full recursion.
- [ ] Progress/rate/ETA reported for long jobs.
- [ ] Largest folders/files/extensions captured or incomplete scope clearly labeled.
- [ ] Cleanup candidates classified as safe/review/protected/hash-before-delete.
- [ ] Stale prior-scan candidates verified live before deletion or reclaim claims.
- [ ] Duplicate candidates verified by SHA-256, not name/size alone.
- [ ] Duplicate reports state whether deletion was performed, and list extra candidates separately from keep candidates.
- [ ] One primary programmatic pie/donut chart produced for artifact reports unless not useful.
- [ ] No deletion/move performed without explicit approved target list.
- [ ] Deletion, if performed, was measured before/after and verified.
