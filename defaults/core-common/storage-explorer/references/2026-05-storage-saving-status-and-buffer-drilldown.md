# Storage Saving Status + Buffer Drilldown Lessons — 2026-05

## Trigger

Use this reference when Xan asks for status on a storage-saving / cleanup effort, especially after multiple cleanup passes across BIGGIE, Buffer & Backups, Plex, Recycle Bin, or backup folders.

## Status Report Pattern

When reporting progress, separate three things clearly:

1. **Current drive state** — live free/used/total from Windows host metrics.
2. **Reclaim tracker** — cumulative session/workstream estimate. Label it as an operational tracker, not byte-perfect accounting, when historical categories overlap.
3. **Remaining target** — pending folder or cleanup class, with risk bucket and next action.

Preferred shape:

```text
## Current drive state
- C: ...
- D: ...
- F: ...

## Reclaimed so far
- Approx total: ...
- Known wins: ...
- Accounting caveat: ...

## Completed
- ...

## Remaining target
- active todo / folder / reason it is not safe to delete broadly

## Next best action
- bounded drilldown / manifest / approval gate
```

## Buffer & Backups Lessons

`D:\Buffer & Backups` is not a safe broad deletion target. Treat it as a mixed archive/backup swamp until classified.

Protect by default:

- family/personal videos such as `Videos_Abuelos`
- phone camera folders
- WhatsApp databases
- current or unique server backups

Review-first:

- `Backups`
- `Plex`
- old server backups
- app/runtime snapshots
- old archives

Likely cleanup, after narrowed inspection:

- stale POP-backup leftovers
- duplicate server backups after hash verification
- installers, ISOs, models, and generated artifacts that are not still needed
- generated Plex/cache material if confirmed as reproducible

## Bounded Drilldown Discipline

If live recursive sizing times out:

- Do not keep retrying the same unbounded command.
- Fall back to immediate-child metadata listing.
- Drill only into the largest unknown children.
- Use per-child timeout and mark timed-out children as `needs drilldown`, not as zero or unknown junk.
- If Windows `diskusage.exe` requires admin, report that limitation and use other Windows-native methods instead of making a false claim.

## WSL -> PowerShell Quoting Pitfall

When invoking PowerShell through WSL shell, wrap the PowerShell script in single quotes at the outer shell layer or escape `$`. Otherwise Bash expands `$_`, `$drives`, and similar variables before PowerShell sees them, producing nonsense like `/home/xantastique.Name` in the command.

Good pattern:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command '$drives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Name -in @("C","D","F") }; $drives | ConvertTo-Json'
```

Bad pattern:

```bash
powershell.exe -Command "$drives = ... $_.Name ..."
```

The lesson is not “PowerShell failed”; the lesson is shell-boundary quoting. The shell is not your friend. It is a clerk with a knife.
