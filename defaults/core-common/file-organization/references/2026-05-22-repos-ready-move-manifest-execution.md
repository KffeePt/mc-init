# Repos Ready-Move Manifest Execution Pattern — 2026-05-22

## Context

Xan asked to organize a misplaced mixed `repos` folder under Windows Documents. The workflow produced a dry-run manifest, then executed only entries marked ready, leaving review-required items in place.

This reference captures reusable lessons for future folder/code-project organization work. It is not a task log; it is the operating pattern that survived contact with Windows.

## Durable Pattern

1. **Inspect and classify first.**
   - For vague containers such as `repos` / `Repos`, run a bounded tree/classification pass.
   - Classify using marker files plus extension dominance and sample paths.
   - Correct obvious classifier mistakes manually before any move manifest is generated.

2. **Check case-near paths on Windows.**
   - `repos` and `Repos` may resolve to the same directory on the default Windows filesystem.
   - Verify parent directory entries directly before assuming two distinct folders exist.
   - Record the conclusion in the manifest so later execution does not duplicate work.

3. **Generate a dry-run manifest.**
   Manifest entries should include:
   - source path, destination path, action, reason
   - risk label
   - confidence
   - status: `ready`, `review_before_move`, `collision_review_required`, or `source_missing`
   - source/destination existence checks

4. **Separate ready moves from review moves.**
   - Execute only `status == ready` when the user says “move ready files”.
   - Skip review-required items unless the user explicitly includes them.
   - Never delete archives, duplicates, tool residue, or empty folders during a ready-move pass.

5. **Create both apply and restore scripts before execution.**
   - Apply script defaults to dry-run; `-Execute` is required to move.
   - Restore script defaults to dry-run; `-Execute` is required to reverse.
   - Apply script skips existing destinations and missing sources.
   - Restore script skips if destination is missing or original source already exists.

6. **Verify after execution.**
   - For each ready entry: destination exists AND source no longer exists.
   - For each review item: source still exists.
   - Save verification as JSON plus a readable execution summary.

## PowerShell JSON Pitfall

PowerShell `ConvertFrom-Json` treats object keys case-insensitively. JSON keys that differ only by case, such as:

```json
{
  "requested_repos_windows": "...",
  "requested_Repos_windows": "..."
}
```

can fail with a duplicate-key error. Avoid case-only key distinctions in JSON artifacts intended for PowerShell scripts. Use explicit names instead:

```json
{
  "requested_lowercase_path_windows": "...",
  "requested_capitalized_path_windows": "..."
}
```

This is not optional hygiene. It is Windows quietly placing a rake in the grass.

## Recommended Artifact Set

```text
MoveManifest.json
MoveManifest.md
ApplyApprovedMoves.ps1
RestoreMoves.ps1
VerificationAfterReadyMoves.json
ReadyMovesExecutionSummary.md
Summary.txt
```

## Verification Shape

```text
ReadyChecked: N
VerifiedMoved: N
Problems: []
ReviewItemsStillPresent: N
```

Problems should include any ready source that still exists or any ready destination that does not exist after execution.

## What Stayed in Review in This Session

Review classes included:
- probable duplicate/experiment copy
- mixed/weak project classification
- loose archives
- empty/near-empty folders
- repo-manager/tool residue

These categories should remain review-required in future runs unless Xan explicitly overrides them.
