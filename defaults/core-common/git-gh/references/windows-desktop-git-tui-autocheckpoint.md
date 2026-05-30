# Windows Desktop Git TUI + Auto-Checkpoint Pattern

Session lesson: consolidating ad-hoc Desktop `.bat` Git launchers into a production-ish TUI exposed a few durable safety rules for Windows-host repos.

## Pattern

Use a single Git TUI for human operations and a separate scheduled `AutoSync` mode for unattended checkpointing.

Human TUI should provide:

- status/log view
- safe checkpoint now
- safe pull (`fetch` + `pull --ff-only`) for non-destructive updates
- destructive force reset guarded by typed confirmation, not a single-key prompt
- destructive rollback guarded by typed confirmation
- scheduled-task studio for installing/removing checkpoint task

Unattended AutoSync should:

1. Ensure the repo exists and the remote exists.
   - Do not blindly run `git remote set-url origin ...`; if `origin` is absent, add it first.
2. Keep its own logs outside the tracked repo, or ignore them before the first checkpoint.
   - Otherwise the autosync dirties the working tree while it is trying to make it clean.
3. Stage and commit local state first if dirty.
4. Create a timestamped checkpoint tag, e.g. `checkpoint/yyyyMMdd-HHmmss`.
5. Fetch and attempt `pull --rebase`.
6. Push the branch and checkpoint tag.
7. Prune checkpoint tags older than the retention window, both local and remote.

## Conflict safety

Scheduled/autonomous mode must never run `reset --hard` or force-push as a recovery maneuver.

On rebase conflict:

- abort the rebase if possible
- preserve local work on a timestamped conflict branch
- attempt to push that branch
- log and exit non-zero
- leave destructive cleanup for a human-confirmed interactive step

## Verification checklist

Before calling this production-ready:

- PowerShell parser check passes for every `.ps1`/`.psm1` touched.
- Scheduled task is registered and points at the expected script path.
- `git remote -v` shows the expected remote before the first autosync run.
- Generated logs are outside the repo or ignored/untracked.
- One non-destructive autosync run creates/pushes a checkpoint tag.
- Rollback/reset paths are only tested up to the confirmation gate unless explicit approval is given.

## Pitfall

A failed first autosync can leave a temporary local conflict branch. Deleting it is destructive enough to require explicit approval; if approval times out, stop and report the partial state instead of trying to route around the guard.
