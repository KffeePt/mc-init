# POP Backup Certain-Trash Removal Pattern — 2026-05-26

## Trigger

Use this pattern when Xan asks to remove trash from an old backup tree after a prior dry-run manifest exists, especially for stale Linux/Windows Downloads backups, extracted app payloads, installer images, and dependency/vendor trees.

## What Worked

1. **Show the remove list first.**
   - Even when the user says items are “certainly useless,” produce an explicit removal manifest before deletion unless an already-reviewed manifest is being approved.
   - Summarize total count/size and top targets in chat; put full detail in CSV/Markdown artifacts.

2. **Keep the certainty filter conservative.**
   - Safe-to-propose classes in old backup Downloads:
     - old OS/live ISO images (`.iso`)
     - old installer/package files (`.deb`, `.rpm`, `.AppImage`, etc.)
     - extracted application/vendor payloads under a backed-up app tree, e.g. `Downloads\Postman\app\resources\app\node_modules\`
     - rebuildable dependency/cache files (`node_modules`, `.cache`, `__pycache__`, `.pytest_cache`)
   - Exclude by default:
     - models/checkpoints
     - archive duplicate candidates that need hashing
     - personal media / phone/family backup content
     - generic review buckets

3. **Use a guarded execution script.**
   - Read the approved CSV manifest.
   - Prefix-guard every path to the intended root.
   - Check each target is still a file.
   - Delete only manifest-listed files.
   - Write result JSON and failure CSV.
   - Print progress every N items with rate.

4. **Verify by manifest re-check, not just free-space telemetry.**
   - Re-check every manifest path after deletion and report remaining count.
   - Count failures/skips separately.
   - Disk free-space APIs can lag or be stale inside the same PowerShell process; treat file-level verification as authoritative, and use a separate post-run `Get-Volume` check only as supporting telemetry.

5. **Directory cleanup is a separate pass.**
   - File deletion leaves empty vendor/dependency directories behind.
   - Generate an empty-directory manifest after deletion.
   - Do not remove directories unless the user approves that directory-specific pass.

## Artifact Set

Recommended files under `C:\Users\santi\Documents\Hermes\Artifacts\YYYY-MM-DD\HH-MM-SS\<Purpose>\`:

- `<Purpose> Remove List.md`
- `<Purpose> Remove List.csv`
- `<Purpose> Paths.txt`
- `<Purpose> WSL Paths.txt`
- `Execute <Purpose> Removal.ps1`
- `<Purpose> Removal Result.json`
- `<Purpose> Removal Failures.csv`
- `<Purpose> Removal Report.md`
- `<Purpose> Empty Directories After Removal.csv`
- `<Purpose> Bundle.zip`

## PowerShell Quoting Pitfall

When creating `.ps1` from WSL/Python, avoid escaped quotes like `\"` inside the written script unless intentional. They can survive into the script and break parsing. Prefer single-quoted defaults in PowerShell parameters:

```powershell
param(
  [string]$Manifest = 'POP Backup Certain Trash Remove List.csv'
)
```

When invoking PowerShell from WSL through `terminal`, avoid inline one-liners containing `$_.Property` unless carefully single-quoted; the Linux shell can expand `$` and corrupt the command. For non-trivial PowerShell, write a small `.ps1` artifact and run it.

## Verification Lines to Report

- processed rows
- deleted / skipped / failed
- remaining manifest files
- deleted GiB from item lengths
- elapsed time and delete rate
- post-run free-space check if available
- empty-dir count if scanned

## Example Outcome

A POP backup cleanup deleted 19,786 approved files totaling 24.1025 GiB by file length, with 0 skips, 0 failures, and 0 remaining manifest files. A follow-up empty-dir scan found 3,547 empty directories; those were left untouched pending separate approval.
