---
name: git-gh
description: "Comprehensive CLI skill for all things git and gh CLI — manage repos locally and on GitHub, branches, PRs, issues, releases, actions, gists, and workflows. Use when Xan asks to do anything with git repositories or GitHub operations."
version: 1.0.0
author: Wilson / Hermes Agent
license: MIT
platforms: [windows, wsl, linux]
metadata:
  hermes:
    tags: [git, github, gh-cli, repos, version-control, branches, PRs, issues, releases]
    related_skills: [github-auth, github-pr-workflow, github-code-review, github-issues, github-repo-management, codebase-inspection]
---

# Git-GH — Git & GitHub CLI

## Overview

Unified skill for all local git operations and GitHub cloud operations via `gh` CLI. Use this instead of loading multiple granular GitHub skills when the task spans both local repo work and GitHub cloud interactions.

Covers: repo init/clone/fork, branching, commits, merging, rebasing, stashing, remote management, PR lifecycle, issues, releases, actions/workflows, gists, and auth.

## When to Use

Use this skill when Xan asks to:

- Initialize, clone, fork, or manage git repositories
- Create/switch/merge/delete branches
- Stage, commit, push, pull, fetch, rebase
- Manage remotes and authentication
- Create/manage GitHub pull requests (create, list, review, merge, close)
- Create/manage GitHub issues (create, list, label, assign, close)
- Create/manage GitHub releases and tags
- View/trigger GitHub Actions workflows
- Create/manage GitHub gists
- Check repo status, diffs, logs, blame
- Resolve merge conflicts
- Stash/unstash changes
- Squash, cherry-pick, amend commits
- Set up GitHub auth (tokens, SSH, gh CLI login)

Do NOT use for:
- GitHub code review — prefer `github-code-review` for structured PR reviews
- Large-scale repo management/organization — still use this skill as primary

## Git Quick Reference

### Repo Setup
```bash
git init [directory]                              # Initialize new repo
git clone <url> [directory]                       # Clone remote repo
gh repo create <name> --public --clone             # Create on GitHub + clone
gh repo fork <owner/repo> --clone                  # Fork + clone
```

### Status & Info
```bash
git status                                         # Working tree status
git log --oneline -n 20                            # Recent commits
git diff                                           # Unstaged changes
git diff --staged                                  # Staged changes
git blame <file>                                   # Line-by-line authorship
git remote -v                                      # List remotes
```

### Branching
```bash
git branch                                         # List local branches
git branch -a                                      # List all branches
git branch <name>                                  # Create branch
git switch <branch>                                # Switch branch
git switch -c <name>                               # Create + switch
git merge <branch>                                 # Merge into current
git rebase <branch>                                # Rebase onto branch
git branch -d <name>                               # Delete local branch
git push origin --delete <name>                    # Delete remote branch
```

### Staging & Commits
```bash
git add <file>                                     # Stage file
git add -A                                         # Stage everything
git add -p                                         # Stage interactively
git commit -m "message"                            # Commit staged
git commit --amend -m "new message"                # Amend last commit
git commit --amend --no-edit                       # Amend without changing message
```

### Remote Operations
```bash
git remote add <name> <url>                        # Add remote
git remote set-url <name> <url>                    # Change remote URL
git fetch <remote>                                 # Fetch without merging
git pull                                           # Fetch + merge
git pull --rebase                                  # Fetch + rebase
git push                                           # Push current branch
git push -u origin <branch>                        # Push + set upstream
git push --force-with-lease                        # Safe force push
```

### Undoing
```bash
git restore <file>                                 # Discard unstaged changes
git restore --staged <file>                        # Unstage file
git reset HEAD~1                                   # Undo last commit, keep changes
git reset --hard HEAD~1                            # Undo last commit, discard changes
git revert <commit>                                # Revert a commit (safe)
git stash                                          # Stash changes
git stash pop                                      # Apply + drop latest stash
git stash list                                     # List stashes
```

### Advanced
```bash
git cherry-pick <commit>                           # Apply specific commit
git rebase -i HEAD~N                               # Interactive rebase last N commits
git bisect start                                   # Start binary search for bug
git reflog                                         # Recovery log
```

## gh CLI Quick Reference

### Auth
```bash
gh auth login                                      # Interactive login
gh auth status                                     # Check auth state
gh auth token                                      # Show token (be careful)
```

### Repos
```bash
gh repo create <name> --public --clone             # Create on GitHub + clone
gh repo create <name> --private --clone            # Private repo
gh repo clone <owner/repo>                         # Clone
gh repo fork <owner/repo> --clone                  # Fork + clone
gh repo view <owner/repo>                          # View repo in browser
gh repo delete <owner/repo> --yes                  # Delete repo (dangerous)
gh repo list                                       # List your repos
gh repo list <owner>                               # List someone's repos
gh repo archive <owner/repo> -y                    # Archive repo
```

### PRs
```bash
gh pr create --title "title" --body "description"  # Create PR
gh pr create --web                                 # Create PR in browser
gh pr list                                         # List PRs
gh pr view [<number>]                              # View PR details
gh pr checkout <number>                            # Checkout PR locally
gh pr review <number> --approve                    # Approve PR
gh pr review <number> --comment -b "feedback"      # Comment on PR
gh pr review <number> --request-changes -b "why"   # Request changes
gh pr merge <number> --squash                      # Merge PR (squash)
gh pr merge <number> --rebase                      # Merge PR (rebase)
gh pr merge <number> --merge                       # Merge PR (merge commit)
gh pr close <number>                               # Close PR
gh pr diff <number>                                # View PR diff
gh pr checks <number>                              # View CI checks
gh pr ready <number>                               # Mark draft PR as ready
```

### Issues
```bash
gh issue create --title "title" --body "details"   # Create issue
gh issue list                                      # List issues
gh issue list --label "bug"                        # Filter by label
gh issue view <number>                             # View issue
gh issue close <number>                            # Close issue
gh issue reopen <number>                           # Reopen issue
gh issue comment <number> --body "comment"         # Add comment
gh issue edit <number> --add-label "bug"           # Add label
gh issue edit <number> --remove-label "wontfix"    # Remove label
gh issue edit <number> --assignee "@me"            # Assign
```

### Releases
```bash
gh release create <tag> --title "title" --notes "notes"  # Create release
gh release create <tag> --generate-notes                  # Auto-generate notes
gh release list                                   # List releases
gh release view <tag>                             # View release
gh release download <tag>                         # Download release assets
gh release delete <tag> -y                        # Delete release
```

### Actions / Workflows
```bash
gh run list                                       # List workflow runs
gh run view <run-id>                              # View run details
gh run watch <run-id>                             # Watch run progress
gh run rerun <run-id>                             # Rerun workflow
gh workflow list                                  # List workflows
gh workflow run <name>                            # Trigger workflow
gh workflow view <name>                           # View workflow details
```

### Gists
```bash
gh gist create <file> --public                    # Create public gist
gh gist create <file> --desc "description"        # Create with description
gh gist list                                       # List your gists
gh gist view <id>                                  # View gist
gh gist edit <id>                                  # Edit gist
gh gist delete <id>                                # Delete gist
```

### Search
```bash
gh search repos "<query>"                         # Search repos
gh search issues "<query>"                        # Search issues
gh search prs "<query>"                           # Search PRs
```

## Common Workflows

### Windows Desktop TUI + Scheduled Checkpoints

For Windows-host Desktop repos with ad-hoc `.bat` Git launchers, prefer consolidating into one human Git TUI plus one unattended checkpoint mode instead of keeping multiple destructive scripts scattered on Desktop.

Use the detailed pattern in `references/windows-desktop-git-tui-autocheckpoint.md`.

Key rules:

- Ensure `origin` exists before `git remote set-url`; absent remotes make scheduled sync fail in ugly, preventable ways.
- Keep scheduled-sync logs outside the tracked repo or ignore them before the first checkpoint. A sync script that writes tracked logs dirties its own working tree. Little ouroboros. Bad pet.
- Scheduled/autonomous checkpointing may commit, tag, fetch, rebase, and push, but must not hard-reset or force-push.
- Destructive human actions such as force reset, rollback, branch deletion, and force push require typed confirmation, not a single-key menu choice.
- Checkpoint rollback should use timestamped tags such as `checkpoint/yyyyMMdd-HHmmss` and a retention window, commonly 31 days for “about a month.”
- If an autosync conflict branch is created during recovery, deleting it is still destructive; stop for approval if confirmation is unavailable or times out.

### New Feature (branch → PR → merge)
```bash
git switch -c feature/name
# ... make changes ...
git add -A && git commit -m "feat: description"
git push -u origin feature/name
gh pr create --title "feat: description" --body "## Changes\n- ..."
```

### Quick Fix
```bash
# ... make changes directly on branch ...
git add -A && git commit -m "fix: description"
git push
```

### Sync Fork with Upstream
```bash
git remote add upstream <original-repo-url>
git fetch upstream
git switch main
git merge upstream/main
git push origin main
```

### Personal/Desktop State Repo with Remote Checkpoints

Use this pattern when a user wants a clutter-prone folder, such as a Desktop, backed by Git without tracking every random file:

1. **Use a reverse-whitelist `.gitignore`.** Ignore `*` by default, then explicitly unignore only canonical launchers, docs, config, and script trees. Re-ignore logs/status/temp/archive outputs even inside whitelisted trees.
2. **Remove noncanonical tracked files from Git without deleting them from disk.** Use `git rm --cached` for tracked clutter; verify with `git ls-files` and `git status --ignored --short`.
3. **Create checkpoint commits and tags.** Use timestamped tags such as `checkpoint/YYYYMMDD-HHMMSS` and push both the branch and tags to the remote.
4. **Retention belongs in the checkpoint script.** Prune old `checkpoint/*` tags locally and remotely after the desired rollback window.
5. **Scheduled autosync must never hard reset.** It may stage/commit/tag/push. If fetch/pull/rebase fails, preserve the local checkpoint and exit loudly; do not switch branches or create conflict branches unless the remote is reachable and the conflict-preservation push can succeed.
6. **Destructive interactive actions require typed confirmation.** Single-key menus are fine for safe actions, but force reset, rollback, key regeneration, branch deletion, and scheduled-task deletion need explicit typed tokens.
7. **Validate the remote before trusting autosync.** `git remote -v` is not enough; check that the repo exists and is reachable (`gh repo view`, `git ls-remote`, or equivalent). Empty newly-created remotes need first-push handling rather than a blind `pull --rebase`.

Reference: `references/desktop-state-checkpoint-repo.md` captures the detailed workflow and pitfalls from Xan's Desktop TUI/checkpoint setup.

### Resolve Merge Conflict
```bash
git merge <branch>                                # Conflict occurs
# ... edit conflicting files, remove markers ...
git add <resolved-files>
git commit                                        # Complete merge
```

## WSL-Specific Notes

- Git repos on Windows drives (`/mnt/c/...`, `/mnt/d/...`) are slower than WSL-native paths
- `gh auth login` works from WSL; it opens a browser on Windows host
- Use `git config --global core.autocrlf input` on WSL to avoid line-ending chaos
- When using SSH keys from WSL, ensure `~/.ssh/config` is set up for GitHub
- `gh` CLI reads `~/.config/gh/hosts.yml` for auth tokens
- Windows paths in git commands: use `/mnt/c/Users/...` from WSL, not `C:\Users\...`

## Common Pitfalls

1. **Force push to main/master.** Never `git push --force` to shared branches without explicit approval. Use `--force-with-lease` as a safer alternative.
2. **Committing secrets.** Always check diffs before committing. Use `.gitignore` to exclude `.env`, keys, tokens, and credential files. When committing generated archives or copied helper scripts, scan both staged text and archive contents for concrete credentials before commit. If you sanitize a helper after building an archive, rebuild the archive and rescan it before committing. A clean source tree with a dirty ZIP is still a leak; it just wears a little compressed hat.
3. **Large files.** Don't commit files > 100MB. Use Git LFS or `.gitignore`. GitHub rejects pushes with files > 100MB.
4. **Merge commit spam.** Prefer squash-merge for feature branches, rebase for clean history on personal branches.
5. **gh auth tokens in scripts.** Never hardcode `gh auth token` output in scripts. The `gh` CLI manages tokens automatically once logged in.
6. **Detached HEAD.** If you see "detached HEAD" after checking out a tag or commit, create a branch to save work: `git switch -c new-branch-name`.
7. **Stale remotes.** After deleting a remote branch, run `git remote prune origin` to clean local tracking references.
8. **Windows scheduled Git sync quirks.** In Windows PowerShell scheduled-task scripts, validate the exact `RunLevel` enum (`Limited` or `Highest`; not informal names like `LeastPrivilege`) and parse-check scripts before registering the task. For Desktop repos, confirm `origin` exists and generated logs are ignored/outside the repo before the first automated checkpoint run.

## Verification Checklist

- [ ] `git status` shows expected branch and clean/modified state
- [ ] `gh auth status` confirms GitHub authentication
- [ ] Remotes point to correct repos (`git remote -v`)
- [ ] No secrets in staged changes (`git diff --staged`)
- [ ] PR/issue number confirmed before merging/closing
- [ ] CI checks passing before merge (`gh pr checks`)
