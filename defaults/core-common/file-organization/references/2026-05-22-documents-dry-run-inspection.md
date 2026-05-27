# 2026-05-22 Documents Organization / Dry-Run Inspection Pattern

## Context

Xan asked to organize Windows Documents through WSL. Earlier plan identified Windows Documents as the real target, not WSL `~/Documents`, and did a safest execution pass first.

Target used:

```text
Windows: C:\Users\santi\Documents
WSL: /mnt/c/Users/santi/Documents
```

Artifact pattern used:

```text
C:\Users\santi\Documents\Hermes\Artifacts\YYYY-MM-DD\HH-MM-SS\DocumentsSafestMoves\
C:\Users\santi\Documents\Hermes\Artifacts\YYYY-MM-DD\HH-MM-SS\DocumentsDryRunInspection\
```

## Safe Execution Pass

User approved starting with safest bets. Actual move pass only touched low-risk items:

- school/work documents
- spreadsheets
- presentations
- archive file
- empty/test folders
- temporary Office lock file
- duplicate-candidate image copies

Explicitly not touched:

- `keys`
- `fort-knox`
- `Obsidian Vault`
- code/project folders
- PowerShell/Windows profile folders
- normal media folders
- Desktop

Generated:

- `MoveManifest.json`
- `SafestMovesReport.md`
- `RestoreSafestMoves.sh`
- `Summary.txt`
- MP3 summary

Verification pattern:

- ensure destination exists
- ensure original root source no longer exists
- skip collisions, never overwrite

## Dry-Run Inspection Request

Xan then requested no moves, only inspection/planning for:

- removing `fort-knox` completely
- organizing `keys`
- organizing `Obsidian Vault`
- moving all repos/projects into `Source`
- organizing code projects by language
- leaving media folders alone except flagging out-of-place files
- detecting duplicates

Important: even when the user says deletion is desired, if they also asks for dry-run/planning, deletion remains a proposed action only.

## Findings from the session

Dry-run reported:

- `fort-knox`: single huge file around 50 GB; propose complete deletion only after approval.
- `keys`: single ~5 MB file; propose move to credentials bucket.
- `Obsidian Vault`: small vault with Obsidian config/plugin files; propose move to personal records/knowledge bucket and warn app path may need update.
- 49 project candidates found.
- 15 root out-of-place files.
- 66 media-folder anomalies, mostly saved web-page debris under Pictures.
- 16 exact duplicate groups, including WhatsApp image copies and web page assets.

## Technique: bounded scan after timeout

A first broad scan timed out. Durable lesson: personal folders can contain deep dependency trees, repo histories, model folders, cache trees, or saved web pages. Do not brute-force a full walk by default.

Bounded scan approach:

- limit files per candidate project
- limit directory depth
- exclude dependency/cache folders
- exclude `Hermes/Artifacts` from duplicate scans
- classify projects from direct children of code roots first
- hash duplicates only for relevant document/media extensions and bounded file sizes

Useful exclusions:

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

## Project classification correction

Initial quick classifier misclassified some projects because it did not account well enough for Dart/Flutter and Swift. Fix before presenting final plan.

Add/consider buckets:

```text
Dart_Flutter
Swift
Rust
Go
Python
JavaScript_TypeScript
C_CPP
Docs_Markdown
Unknown_Mixed
```

Heuristics that helped:

- `.dart`, `pubspec.yaml`, or folder name containing `flutter` -> `Dart_Flutter`
- `.swift` -> `Swift`
- `.rs` or known Rust repo names -> `Rust`
- marker files should outweigh incidental assets/docs
- docs-heavy repos may be incorrectly classified as markdown if scan depth is too shallow

## Reporting Style That Worked

Telegram summary should be compact:

```text
Dry-run inspection done. No files moved. No files deleted.

Found:
- fort-knox: huge file; delete only after approval
- keys: move to credentials bucket
- Obsidian Vault: move to personal records bucket
- Projects: N candidates into Source/<Language>/<Project>
- Duplicates: N exact-hash groups
- Media anomalies: mostly saved webpage debris

Artifacts:
- Windows -> ...
- WSL -> ...
```

Keep full lists in artifacts, not chat, unless Xan asks for them.
