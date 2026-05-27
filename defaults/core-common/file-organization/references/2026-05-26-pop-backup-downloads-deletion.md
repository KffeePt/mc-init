# POP Backup Downloads Deletion and Reclaim Accounting

Session pattern from 2026-05-26.

## Trigger

Use this when Xan approves deletion of stale backup Downloads, duplicate leftovers, installer packages, or old backup sediment after a manifest/review pass.

## Key distinction

When Xan says "remove Downloads" in the context of `POP-backup`, interpret it as the stale backed-up Downloads tree, **not** the live Windows user Downloads folder.

Safe target used:

```text
D:\Buffer & Backups\Backups\POP-backup\Downloads
/mnt/d/Buffer & Backups/Backups/POP-backup/Downloads
```

Do not generalize this to `C:\Users\santi\Downloads` without explicit confirmation.

## Deletion pattern

1. Confirm the target path is exactly under the intended stale backup root.
2. Create an artifact folder under `C:\Users\santi\Documents\Hermes\Artifacts\YYYY-MM-DD\HH-MM-SS\...`.
3. Walk the target first and write a deletion manifest with path, bytes, and mtime.
4. Delete the approved tree or manifest rows.
5. Verify the target/manifest paths are gone.
6. Write `Deletion Result.json` with:
   - status
   - target
   - deleted file count
   - deleted dir count
   - deleted bytes/GiB from pre-delete file lengths
   - elapsed time
   - remaining_exists
   - errors/error_count
   - manifest path
7. Update `STATE.md` with intent, tools, artifacts, verification, and remaining work.

## User-specific preservation rule

For POP-backup review cleanup, preserve Minecraft/server backups when Xan says to keep server backups. Mark those rows as `keep_server_backup`, even if they appear in archive/log or broad review buckets.

## Reclaim accounting

For the 2026-05-26 POP-backup cleanup chain, grounded reclaimed categories were:

- old model/checkpoint files
- old model Git LFS objects
- exact duplicate extras
- stale POP-backup Downloads tree

Keep reclaim math separated by category. Disk free-space APIs may lag; trust actual pre-delete byte counts as primary accounting.

## Pitfalls

- Do not delete broad review/media/personal buckets just because the backup is old.
- Do not mix server backups into the same deletion action after Xan says to keep them.
- Do not call name/size duplicate candidates safe unless exact hashes were verified.
- Empty directories left after file deletion are a separate cleanup pass unless the approved target is the whole stale tree.
