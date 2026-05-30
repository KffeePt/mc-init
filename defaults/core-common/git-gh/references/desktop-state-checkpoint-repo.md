# Desktop State Checkpoint Repo Pattern

Session source: Xan's Windows Desktop TUI consolidation and autosync hardening, 2026-05-30.

## Problem class

A user wants a volatile/clutter-prone folder, especially a Windows Desktop, backed by Git for remote autosave and rollback, while allowing random local clutter without polluting repo state.

## Durable pattern

### 1. Reverse-whitelist Git tracking

Use `.gitignore` as a whitelist, not a blacklist:

```gitignore
*
!.gitignore
!git_manager.bat
!plex_manager.bat
!docs/
!docs/**
!ps1/
!ps1/git_manager/
!ps1/git_manager/**
!ps1/plex_manager/
!ps1/plex_manager/**

# generated outputs stay ignored even under whitelisted trees
ps1/logs/
ps1/logs/**
ps1/plex_manager/logs/
ps1/plex_manager/logs/**
*.log
*.tmp
*.bak
*.zip
```

Then remove already-tracked clutter without deleting local files:

```powershell
git rm --cached -- <path>
git rm --cached -r -- <folder>
```

Verification:

```powershell
git ls-files
git status --ignored --short
```

Expected shape: `git ls-files` contains only canonical docs/scripts/launchers; ignored status shows Desktop clutter and generated logs.

### 2. Checkpoint commits + checkpoint tags

Checkpoint operation:

1. `git add -A`
2. commit if dirty
3. create/force timestamped tag: `checkpoint/YYYYMMDD-HHMMSS`
4. fetch remote
5. if remote branch exists, pull/rebase safely
6. push branch
7. push checkpoint tag
8. prune checkpoint tags older than retention window locally and remotely

Use tags as rollback handles because they are cheap, visible, and easy to push independently of branch history.

### 3. Scheduled autosync safety

Scheduled autosync must not be allowed to perform destructive recovery. It should:

- create a local checkpoint before attempting remote operations
- verify remote reachability
- handle empty new remotes as first-push cases
- push branch and checkpoint tag
- fail loudly when remote operations fail
- preserve local state and logs for manual repair

Do **not** let scheduled autosync run `reset --hard`, delete files, overwrite keys, or force-push rollback state.

### 4. Remote failure pitfall

Do not treat `git remote -v` as proof the remote exists. The remote URL can be configured while the GitHub repo does not exist or is inaccessible.

Check one of:

```powershell
gh repo view OWNER/REPO --json name,visibility,sshUrl
git ls-remote --heads origin main
```

If the remote repo is missing, create/fix it before running autosync. If `fetch` fails, preserve the local checkpoint and stop. Avoid branch switching in that failure path; otherwise the tool creates noisy local conflict branches without any remote backup.

### 5. Interactive TUI safety

For menu-driven Git/ops TUIs:

- single-key input is acceptable for safe actions
- typed confirmation tokens are required for destructive actions
- examples: `RESET-DESKTOP`, `ROLLBACK-DESKTOP`, `DELETE-TASK`, `REGEN-SSH-BACKUP`
- destructive SSH key regeneration should back up existing keys before replacement and copy the new public key to clipboard

### 6. Production verification checklist

- PowerShell parser check passes for scripts/modules.
- Scheduled task is registered and points to the intended script.
- Remote exists and is private/expected visibility.
- SSH or gh auth works.
- One autosync run succeeds.
- `main` is pushed.
- latest `checkpoint/*` tag is pushed.
- `git status --short --branch` is clean or expected.
- `git ls-files` shows only canonical whitelist entries.
- `git status --ignored --short` shows local clutter ignored.
