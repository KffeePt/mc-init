# 2026-05-22 Documents folder renaming and Source layout

Session-specific reference for the `file-organization` umbrella skill. Use this as a concrete pattern when Xan asks to execute or review a previous Documents organization plan.

## Context

Target was Xan's Windows Documents folder, accessed from WSL:

- Windows: `C:\Users\santi\Documents`
- WSL: `/mnt/c/Users/santi/Documents`

The work followed earlier dry-run and execution passes, then removed numeric prefixes from the high-level organization buckets and continued source-code classification.

## Durable task lessons

- If Xan asks to “show the previous plan,” do not rely only on chat/session recall. Check saved artifacts first when available; organization work should leave reports/manifests under `Documents/Hermes/Artifacts/YYYY-MM-DD/HH-MM-SS/<PascalCasePurpose>/`.
- Prefer human-readable folder names after execution if numeric prefixes are no longer wanted. Rename buckets cleanly and verify no numbered organization folders remain.
- When reorganizing source folders, finish cleanup of review buckets like `Unknown_Mixed` after classification rather than leaving empty scaffolding behind.
- Treat root `repos` carefully: inspect contents. If it contains only archive files, archive it under a source-archive bucket rather than treating it as active code.
- Dependency-only project remnants, e.g. folders containing only `node_modules`, belong in review/dependency-only rather than active `Source`.

## Concrete moves from this session

Numeric bucket rename pattern:

```text
00_Inbox -> Inbox
01_Important -> Important
02_School_And_Work -> School_And_Work
03_Code_And_AI -> Code_And_AI
04_Media -> Media
05_Games -> Games
06_Archives -> Archives
90_Keep_In_Place -> Keep_In_Place
99_To_Review -> To_Review
```

Source cleanup examples:

```text
Source/Unknown_Mixed/bash -> Source/Shell/bash
Source/Unknown_Mixed/Loose_Files/clnpss.cpp -> Source/C_CPP/Loose_Files/clnpss.cpp
Source/Unknown_Mixed/codebase-management -> To_Review/Dependency_Only/codebase-management
repos -> Archives/Source_Archives/repos
```

## Verification checklist

After this class of execution pass, explicitly verify:

- Remaining numbered organization folders: zero, if numeric prefixes were removed.
- `Source/Unknown_Mixed`: removed or only contains deliberate review items.
- Root `repos`: removed if it was archived.
- Explicit protected folders still exist, e.g. top-level `GitHub`, `Obsidian Vault`, credential/key buckets.
- Manifest/report/restore/audio artifacts exist in the artifact directory.
- Error count is zero or every error is listed with a next action.

## Artifact pattern

Example completed artifact directory:

```text
/mnt/c/Users/santi/Documents/Hermes/Artifacts/2026-05-22/22-32-26/RemoveNumberedFoldersAndSourceOrg
```

Typical files:

```text
RenameAndSourceOrgManifest.json
RenameAndSourceOrgReport.md
RestoreRenameAndSourceOrg.sh
Summary.txt
RenameAndSourceOrgSummary.mp3
```
