---
name: file-organization
description: Use when Xan asks to organize, inspect, sort, clean up, deduplicate, archive, or plan moves/deletions for personal folders such as Documents, Desktop, Downloads, media folders, vaults, keys, code repositories, or mixed Windows/WSL user files.
version: 1.0.0
author: Wilson / Hermes Agent
license: MIT
platforms: [windows, wsl, linux]
metadata:
  hermes:
    tags: [file-organization, cleanup, dry-run, windows, wsl, documents, duplicates, manifests, restore]
    related_skills: [task-artifacts-delivery, personal-server-safety-audit, file-tree-inspection, storage-explorer]
---

# File Organization

## Overview

Use this skill for organizing Xan's file areas: Windows Documents/Desktop/Downloads, WSL home folders, media folders, code/project folders, vaults, credentials/keys, and mixed loose files.

Default assumption on this server: user-facing `~/Documents` requests usually mean the Windows host Documents folder unless the user explicitly says WSL/Linux internals. Resolve Windows paths through `/mnt/c/Users/<user>/...` and report Windows + WSL paths when useful.

Primary objective: produce safe, reversible organization. Do not turn cleanup into data loss wearing a little hat.

## Operating Rules

1. **Plan before changing files.**
   - For multi-step or file/system-changing work, show a short plan summary first unless Xan says `skip plan`.
   - If Xan asks for inspection/dry-run, do not move/delete anything.

2. **Prefer dry-run manifests first.**
   - Generate a proposed move/delete plan with source, destination, reason, collision risk, size, modified time, and whether approval is required.
   - Save durable reports under `Documents/Hermes/Artifacts/YYYY-MM-DD/HH-MM-SS/<Pascal Case Purpose>/`.
   - For Xan's user-facing folders and artifacts, prefer readable space-separated names over underscores. Use underscores only when a tool, repository, package manager, dataset, or code convention requires them.

3. **Never delete on inference alone.**
   - Duplicates require exact hash verification before deletion is proposed.
   - Destructive actions must remain explicit approval items.
   - Large vault/archive-like files should be treated as high-risk unless Xan explicitly confirms deletion.

4. **Preserve sensitive material.**
   - Do not print secrets or file contents from key/vault folders.
   - For `keys`, credential stores, vaults, or suspiciously sensitive names, inspect only metadata unless asked otherwise.
   - Good target pattern: `01_Important/Credentials_And_Keys/` for key material and `01_Important/Personal_Records/` or a knowledge bucket for notes/vaults.

5. **Keep Windows profile folders cautious.**
   - `PowerShell`, `WindowsPowerShell`, `Custom Office Templates`, `desktop.ini`, and known shell/library metadata may affect Windows behavior.
   - Prefer leave-in-place or explicit review over blind moves.

6. **Code/projects need classification, not vibes.**
   - If user approves path breakage, still produce a clear map before moves.
   - Organize repositories under `Source/<Language>/<Project>` when requested.
   - Classify using markers and extensions: `pyproject.toml`, `requirements.txt`, `package.json`, `tsconfig`, `Cargo.toml`, `go.mod`, `pubspec.yaml`, `*.sln`, `CMakeLists.txt`, etc.
   - Watch for false labels in bounded scans: Flutter/Dart, Swift, Rust, docs-heavy repos, monorepos, and generic container folders can be misclassified. Add a review bucket for uncertain projects.

7. **Media folders are not automatically cleanup targets.**
   - Leave normal media folders in place unless Xan asks otherwise.
   - For movie libraries, preferred Plex-friendly folder shape is `D:\Movies\Movie Title (Year)\<media files>`. When asked to normalize movies, generate a manifest + restore script, move only confidently parsed title/year entries, and leave ambiguous loose files in review rather than inventing years. See `references/2026-05-27-movies-folder-normalization.md`.
   - Flag out-of-place files inside media folders: saved web page debris, scripts, archives, datasets, non-media config, and obvious junk.
   - Treat `desktop.ini` as Windows metadata noise, not a cleanup win.
   - For saved browser pages in image folders, move the `.htm/.html` file and its matching asset folder (`<name> Archivos`, `<name>_files`, etc.) together into review/debris; do not delete individual assets because the HTML may reference them.
   - Zero-byte screenshots/images are safe deletion candidates **after approval**, but log them; there is no useful restore payload because they are empty.
   - Data files found in media folders, e.g. `.npy`, should move to a review/data-artifacts bucket rather than being treated as pictures.

8. **Plex TV library rename normalization.**
   - When cleaning torrent-imported TV folders, prefer Plex's live physical `Location` metadata as the authority for show title/year rather than regex-only cleanup of release names.
   - Target top-level show folder format: `Show Title (Year)`.
   - Target second-level format: `Season N (Year)` or `Specials (Year)`; do not leave `S1`, `S01`, raw torrent pack folders, or `Season 01 - Extras` when the user asks for manual normalization.
   - Generate a manifest and restore script before mutation; then apply ready renames, merge/flatten malformed season folders without overwriting, and verify the final tree.
   - If qBittorrent flatten hooks exist, patch them after the manual cleanup so future downloads create/reuse the same `Season N (Year)` folders instead of reintroducing `S1`/`S2`.
   - For manual catch-up flattening while torrents are still active, query qBittorrent's structured API first and build an incomplete/content-path exclusion set. Move only completed show roots; skip `.part` files, active content paths, and any root currently tied to an incomplete torrent.
   - Do not force movie-shaped items in Shows into fake season folders; report them as follow-up moves/review instead.

9. **Generate restore paths/scripts before execution.**
   - For actual move passes, create a manifest and restore script before moving.
   - For manifest-driven moves, also create an apply script that defaults to dry-run and requires an explicit execution flag.
   - Split move statuses into `ready`, `review_before_move`, `collision_review_required`, and `source_missing`; when Xan says “move ready files,” execute only `ready` entries and leave review items untouched.
   - Skip collisions rather than overwrite.
   - Verify post-move: destination exists and source is gone for ready items; review-required items still exist at their original source.

9. **Media automation hooks need adaptive batch barriers.**
   - For qBittorrent/Plex show automation, do not flatten on every individual `torrent finished` event when multiple concurrent downloads may belong to the same show/batch.
   - Use a JSON hashmap registry updated by `torrent added`, keyed by info hash, and guard registry reads/writes with a Windows global mutex; qBittorrent can launch hooks concurrently.
   - Do not rely on a blunt “wait until every active torrent finishes” barrier. Store size/progress/speed/qBittorrent ETA/seeds/peers/availability, compute reliability and ETA groups, then decide whether to wait briefly or flush completed roots now.
   - Flush completed roots when remaining active torrents are long-tail or stalled; wait only when all remaining active items are near-finished and reliable. This prevents a slow torrent from blocking completed library updates.
   - Prefer qBittorrent content path over save path when resolving a show root, hard-refuse to flatten `D:\Shows` itself, and explicitly exclude active/incomplete content paths.
   - Sort/rank torrent jobs by ETA/size/reliability for scheduling only; never arrange Plex media files by size.
   - Query Plex library sections live before hardcoding refresh IDs; stale section IDs silently become 404s.
   - See `references/2026-05-27-qbittorrent-batch-flatten-hooks.md` for the baseline registry shape and `references/2026-05-28-qbittorrent-adaptive-flatten-batching.md` for the adaptive scheduler pattern.

9. **Rename folders cautiously.**
   - User-facing organization folders should use spaces, not underscores, for legibility.
   - Safe rename scope is usually top-level personal containers and known review/archive buckets, e.g. `Important`, `School And Work`, `To Review`, `Archives`, `Media`.
   - Do **not** recursively rename inside `Source`, `GitHub`, repositories, datasets, venvs, `.git`, package/vendor trees, generated web-page asset folders, or application/project internals unless Xan explicitly approves path breakage.
   - For naming cleanup, produce/keep a rename manifest and verify remaining underscore folders only within the approved safe scope.

10. **Interpret exclusions broadly and verify against them.**
   - If Xan says “leave GitHub alone,” do not move top-level `GitHub` **or nested GitHub-named buckets** such as `03_Code_And_AI/GitHub` unless he explicitly narrows the exclusion.
   - After execution, run explicit existence checks for protected/excluded paths and correct any over-broad move immediately.
   - Manifests are not paperwork theatre; use them to detect and reverse mistakes.

## Workflow

### 1. Scope and exclusions

State:

- target root
- paths explicitly untouched
- whether this is dry-run or execution
- whether deletion is allowed or only proposed

For Documents on Xan's machine, likely target:

```text
Windows: C:\Users\santi\Documents
WSL: /mnt/c/Users/santi/Documents
```

### 2. Inspect safely

Collect metadata only unless content inspection is necessary:

- top-level files/folders
- bounded tree view when hierarchy matters; load/follow `file-tree-inspection` for vague containers like `repos`, `projects`, `misc`, `old`, `backup`, or `To_Review`
- Filelight-style disk usage view when size/space matters; load/follow `file-light-inspection` to identify largest folders/files before cleanup or migration
- file counts and approximate sizes
- Windows Recycle Bin metadata when relevant: parse `$I*` records under `$Recycle.Bin` for original path, deletion time, and size; Windows 10/11 `$I` records may store a 4-byte path length at offset 24, so UTF-16 paths often begin at offset 28. Shell COM Recycle Bin columns can be locale/order-dependent and mislabel size/type/date/original-location, so use `$I` parsing for reliable rundowns.
- candidate sensitive folders/files
- project/repo candidates
- media folder anomalies
- duplicate candidates by exact hash
- collisions against proposed destinations

Bound scans to avoid dependency/media explosions. Exclude or limit:

```text
.git
.venv
venv
node_modules
__pycache__
.mypy_cache
.pytest_cache
dist
build
.next
.cache
models
checkpoints
Hermes/Artifacts
```

If a scan times out or returns too much, narrow the scan and record the limitation. Do not brute-force indefinitely.

### 3. Plan moves/deletions

Use action classes:

```text
move
archive_or_merge
delete_after_explicit_approval
leave_in_place
review_required
```

Include a risk label:

```text
low
path_breakage_possible
sensitive_metadata_only
destructive_requires_backup_or_confirmation
windows_profile_behavior_risk
```

### 4. Report compactly

Use Xan's preferred shape:

```text
Summary:
- ...

Proposed:
- ...

Do not touch:
- ...

Approval needed:
- ...

Artifacts:
- Windows -> ...
- WSL -> ...
```

Avoid dumping huge project lists into Telegram unless requested. Put full detail in artifacts and summarize counts + categories in chat.

For responses longer than one paragraph after file organization, cleanup, backup inspection, or artifact delivery work, add a short `TTS summary:` section at the end and generate audio for **that summary only** when feasible. Do not generate TTS for the full response.

Do **not** create separate summary-only artifacts just to hold the spoken summary. Xan wants the human summary in the normal chat response. Zip/report bundles should contain useful reports, manifests, CSV/JSON data, images, or media outputs — not duplicate summary files for ceremony.

For TTS summaries, use plain spoken language. Do not read literal filenames, commands, URLs, paths, IDs, or exact object strings unless explicitly requested; replace them with short labels like `cleanup plan`, `artifact folder`, `backup scan`, or `server config`. Include `Remaining work:` when useful.

### 5. Execute only after approval

When approved:

1. Re-read or regenerate manifest against current state.
2. Create destination skeleton.
3. Write restore script.
4. Move low-risk items first.
5. Move sensitive/project items only if included in approval.
6. Delete only exact approved deletion targets.
7. Verify and report moved/skipped/errors.
8. Re-check explicit exclusions (`GitHub`, vaults, Desktop, etc.) after moves; restore immediately if an exclusion was caught by a broader rule.

Avoid planning both a parent folder and its children as separate moves in the same execution pass. Once the parent moves, child paths become `source_missing`; this is noisy and can hide real skips. Prefer parent-level moves for standalone applications/projects and child-level moves only when the parent is a deliberate container to keep.

## Duplicate, Backup Sediment, and Rebuildable Environment Cleanup

- Group duplicate candidates by size first.
- Hash only candidates within bounded size thresholds unless Xan approves deep scan.
- Exact duplicate = same cryptographic hash.
- Zero-byte duplicate groups are usually junk but still require approval before removal.
- Prefer survivor paths that are organized and semantically named.
- Do not delete originals just because `- Copy` exists; verify exact hash and choose survivor deliberately.
- For approved duplicate deletion, re-hash delete target and survivor immediately before deletion; skip rather than delete if hashes diverge or survivor is missing.
- Treat rebuildable virtual environments as a separate cleanup class from duplicates: delete only approved venv folders, only when dependency manifests exist nearby, and report reclaimed space separately.
- For stale backup “certain trash” cleanup, show an explicit remove list first, then delete only approved manifest rows. Good conservative targets: old OS/live ISOs, old installer packages, extracted application/vendor payloads in backed-up Downloads, and rebuildable dependency/cache files. Exclude models/checkpoints, personal media, phone/family backup content, archive duplicate candidates, and generic review buckets unless separately approved.
- For file-deletion execution, use a guarded manifest-driven script: prefix-check every path to the intended root, check target still exists as a file, write result JSON and failure CSV, report processed/deleted/skipped/failed/remaining counts, elapsed time, rate, and deleted bytes from actual file lengths.
- Verify destructive cleanup by re-checking manifest paths after deletion. Disk free-space APIs may lag or return stale values inside the same PowerShell process; use a separate post-run free-space check only as supporting telemetry.
- Empty directories left after file deletion are a separate cleanup pass. Generate an empty-directory manifest and get approval before deleting directories, even if the files were already approved.

## Project Classification Heuristics

Common buckets:

```text
Source/Python
Source/JavaScript_TypeScript
Source/Dart_Flutter
Source/Rust
Source/Go
Source/C_CPP
Source/DotNet
Source/Java_Kotlin
Source/Swift
Source/Shell
Source/PowerShell
Source/Notebooks_Data
Source/Docs_Markdown
Source/Unknown_Mixed
```

Pitfalls:

- Docs-heavy repos may look like markdown projects even when source exists deeper.
- Flutter projects may be misread if `pubspec.yaml` is missed; include Dart detection.
- Swift and Go can appear inside TypeScript repos; classify by dominant/marker intent, not one file.
- Generic `repos` or `Source` folders are containers, not projects, unless direct contents prove otherwise.
- Monorepos may belong under their primary ecosystem or `Unknown_Mixed` with review.
- On Windows, case-near paths such as `repos` and `Repos` may be aliases to the same directory; verify parent entries before treating them as distinct trees.
- If a manifest JSON will be consumed by PowerShell, avoid object keys that differ only by case; `ConvertFrom-Json` treats keys case-insensitively and can fail on duplicate keys.

## Artifact Requirements

Load/follow `task-artifacts-delivery` when producing durable plans or reports.

Recommended files:

```text
DryRunInspection.json
DryRunMovePlan.md
MoveManifest.json
RestoreMoves.sh
Summary.txt
<ShortAudioSummary>.mp3
```

## Reference Material

- `references/2026-05-23-approved-dedup-and-venv-cleanup.md` — approved deletion execution pattern for exact-hash duplicate archives and rebuildable Python virtual environments: re-hash before deletion, verify survivors, separate reclaimed-space accounting, and compact final reporting.
- `references/2026-05-27-qbittorrent-batch-flatten-hooks.md` — qBittorrent/Plex show automation pattern: torrent-added JSON hashmap registry, mutex-protected batch barrier, defer-until-all-finished flattening, show-root safety checks, name-cleanup regex pitfalls, live Plex section verification.
- `references/2026-05-28-qbittorrent-adaptive-flatten-batching.md` — adaptive improvement to strict batch barriers: rank torrents by size/progress/speed/ETA/seeds/peers, flush completed roots when remaining active torrents are long-tail/stalled, and never let incomplete content paths be flattened.
- `references/2026-05-27-media-library-precheck-and-routing.md` — mixed movie/show acquisition lessons: explicit qBittorrent categories, path-root fallback, pre-add folder/duplicate checks, and wrong-title indexer bait rejection.
- `references/2026-05-27-plex-shows-folder-rename-normalization.md` — Plex TV library cleanup pattern: top-level `Show Title (Year)`, second-level `Season N (Year)`, manifest/restore discipline, malformed torrent folder flattening, hook update to prevent regressions.
- `references/2026-05-26-pop-backup-certain-trash-removal.md` — stale backup cleanup pattern for conservative certain-trash remove lists, guarded PowerShell deletion, manifest re-check verification, and empty-directory follow-up.
- `references/2026-05-26-pop-backup-downloads-review-buckets.md` — stale backup review-bucket marking pattern: derive from latest manifest, mark Downloads installer/runtime packages for approval-only deletion, preserve explicit keep buckets such as server backups, and separate extracted app payloads from installer files.
- `references/2026-05-26-pop-backup-downloads-deletion.md` — approved stale-backup Downloads deletion pattern: exact target guard, pre-delete manifest, result JSON, server-backup preservation, and category-separated reclaim accounting.
- `references/2026-05-23-documents-remaining-work-and-naming.md` — session pattern: carrying prior remaining work forward, bounded GitHub scan, exact-hash Takeshi dataset dedup candidates, venv safety check, and space-separated naming enforcement with safe rename scope.
- `references/2026-05-22-documents-dry-run-inspection.md` — session pattern: safest pass, dry-run inspection, sensitive deletion proposal, Source-by-language planning, duplicate/media anomaly reporting.
- `references/2026-05-22-documents-execution-and-media-cleanup.md` — execution lessons: broad exclusion handling, parent/child project move pitfalls, saved-webpage debris handling, zero-byte screenshot cleanup, and media-folder anomaly moves.
- `references/2026-05-22-documents-folder-renaming-and-source-layout.md` — final execution pattern: removing numeric prefixes, completing Source layout, archiving inactive root `repos`, dependency-only review buckets, and verification checklist.
- `references/2026-05-22-repos-ready-move-manifest-execution.md` — ready-only code-project move execution pattern: case-near Windows path verification, manifest statuses, apply/restore scripts, post-move verification, and PowerShell JSON key pitfalls.
- `references/2026-05-23-review-cleanup-and-filelight.md` — second-pass review cleanup + Filelight lessons: manifest-driven review moves, empty-container quarantine, policy-vs-storage distinction, and explicit remaining-work reporting.
- `references/2026-05-23-windows-recycle-bin-rundown-and-clear.md` — Windows Recycle Bin inspection/clear pattern from WSL: `$I` metadata parsing, top-level vs payload counts, per-drive reclaimed-space accounting, residual metadata verification, and WSL trash follow-up.
