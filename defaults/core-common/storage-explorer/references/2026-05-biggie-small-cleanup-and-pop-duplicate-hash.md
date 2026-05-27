# 2026-05 BIGGIE Small Cleanup and POP Duplicate Hash Lesson

## Context

Session class: BIGGIE storage cleanup + duplicate hash analysis.

Scope covered:

- Guarded cleanup of stale/high-confidence candidates under `D:\`.
- Verification of old duplicate manifest rows before trusting them.
- Targeted SHA-256 duplicate analysis for `D:\Buffer & Backups\Backups\POP-backup`.
- Avoidance of broad WSL traversal after the scan entered disk sleep with no useful progress.

## Durable Lessons

1. **Verify stale cleanup candidates live before acting.**
   - Previously large candidates can disappear between scan and execution.
   - Report absent paths as stale evidence, not as cleaned space.
   - Measure current free space before/after so reclamation claims are grounded.

2. **Do not trust old duplicate manifests as current truth.**
   - Re-check that each candidate path still exists before hashing or deletion.
   - If the old subtree is gone, mark manifest rows stale and stop pursuing them.

3. **For Windows-hosted BIGGIE duplicate hashing, prefer PowerShell targeted same-size grouping.**
   - First group files by size over a threshold.
   - Hash only groups with count > 1.
   - Emit exact duplicate groups, keep candidate, extra candidates, potential reclaim, and hash errors.
   - Do not delete duplicates unless Xan explicitly approves the extra candidates.

4. **Broad WSL `/mnt/d` duplicate hashing is a trap for live Telegram work.**
   - It can enter disk sleep (`Ds`) or crawl with no useful progress.
   - Kill stalled broad crawls and switch to bounded Windows-native scans or persistent background indexing.
   - Capture the stall as a method failure, not a reason to abandon the task.

5. **Small duplicate wins may be below deletion-risk threshold.**
   - Exact duplicates worth ~hundreds of MiB inside backups/build artifacts are real but often low-value.
   - Recommend review/approval instead of deleting backup-adjacent artifacts for trivial reclaim.

## Report Pattern

For this class of work, include:

- current drive free/used/total after action;
- exact cleanup targets attempted;
- current existence check result for each target;
- before/after free-space delta;
- duplicate scan scope and thresholds;
- files considered, same-size groups checked, files hashed, hash errors;
- exact duplicate groups and potential reclaim;
- explicit statement whether duplicates were deleted;
- artifact paths and bundle hash;
- note if broad scan was aborted and why.

## Safe PowerShell Shape

Use this shape conceptually, adapting paths/thresholds per task:

```powershell
$Root = 'D:\Buffer & Backups\Backups\POP-backup'
$MinBytes = 1MB
$files = Get-ChildItem -LiteralPath $Root -File -Recurse -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.Length -ge $MinBytes }

$groups = $files | Group-Object Length | Where-Object { $_.Count -gt 1 }
foreach ($g in $groups) {
  $hashed = foreach ($f in $g.Group) {
    try {
      $h = Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256 -ErrorAction Stop
      [pscustomobject]@{ Path=$f.FullName; Bytes=$f.Length; SHA256=$h.Hash }
    } catch {
      [pscustomobject]@{ Path=$f.FullName; Bytes=$f.Length; SHA256=$null; Error=$_.Exception.Message }
    }
  }
  $hashed | Where-Object SHA256 | Group-Object SHA256 | Where-Object { $_.Count -gt 1 }
}
```

Keep deletion as a separate explicit approved step. The hash pass is evidence collection, not cleanup by implication.
