# Windows Recycle Bin Rundown + Clear Pattern — 2026-05-23

Use this reference when Xan asks what is in the trash/recycle bin, wants per-drive reclaim estimates, or asks to clear all trash bins from a WSL-hosted Hermes session.

## Reliable inspection pattern

- Prefer Windows host inspection for Recycle Bin work, not Linux-only trash assumptions.
- Use `$Recycle.Bin` metadata records for reliable original path, deletion time, size, and drive attribution.
- `$I*` records contain the original path and deleted metadata; on current Windows records, UTF-16 path usually starts at offset 28 when version >= 2, not always offset 24.
- Shell COM columns from `Shell.Application.NameSpace(10)` can be locale/order-dependent and may mislabel size/type/date/original-location. Good for visible count, weak for structured reports.
- Distinguish:
  - top-level deleted items: user-meaningful count
  - payload files inside recycled folders: inflated internal count

## Suggested report shape

- Total top-level deleted items
- Total reclaimable GiB
- By drive: `C:`, `D:`, etc.
- By category: video/media, archives, installers, images, code/config/text, other/folders
- Biggest items with original path and deleted date
- Sensitive/dev-ish tiny files called out separately, without printing contents
- Artifact paths for full CSV/JSON/Markdown report

## Safe clear pattern

1. If the user only asks to inspect, do not delete.
2. If the user asks to clear, use Windows host Recycle Bin first:
   - `Clear-RecycleBin -Force`
3. Verify using both:
   - `Shell.Application.NameSpace(10).Items().Count` for visible Recycle Bin items
   - residual `$Recycle.Bin` byte counts for system metadata
4. Clear WSL freedesktop trash separately:
   - `~/.local/share/Trash/files`
   - `~/.local/share/Trash/info`
5. Avoid long recursive `find`/`du` over trash trees after a clear; it can time out on pathological/deep entries. For verification, top-level `os.listdir` counts are enough unless the user asks for forensic detail.
6. Report residual Windows `$Recycle.Bin` metadata as normal if only bytes remain. Do not treat system metadata skeletons as failed cleanup.

## Per-drive saved-space accounting

- Capture before-clear GiB by drive from `$Recycle.Bin` inspection.
- After clear, subtract residual byte counts by drive.
- Round per-drive savings to two decimals for Telegram.
- State that residual bytes are metadata, not meaningful storage.

## Pitfalls observed

- `$` in PowerShell paths from WSL must be escaped carefully; otherwise `C:\$Recycle.Bin` becomes mangled by shell interpolation.
- PowerShell output may show `0 GiB` for byte-scale metadata; keep raw bytes in JSON artifacts.
- A global clear can reclaim space from multiple drives, not just `C:`.
- Recycle Bin contents may include tiny credential/config-looking files (`.env`, SDK JSON, `.git`, locks). These usually do not matter for space, but call them out before a blind purge if doing an inspection report.
