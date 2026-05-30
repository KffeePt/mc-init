---
name: file-tree-inspection
description: Use when organizing, exploring, auditing, mapping, or triaging a folder tree; when the user asks to see a whole folder's contents, subfolders, or files; or before moving scattered projects/files where hierarchy matters.
version: 1.0.0
author: Wilson / Hermes Agent
license: MIT
platforms: [windows, wsl, linux]
metadata:
  hermes:
    tags: [file-tree, inspection, organization, mapping, folders, inventory]
    related_skills: [file-organization, codebase-inspection]
---

# File Tree Inspection

## Overview

Use this skill to produce a bounded, readable view of a folder's structure before organizing, exploring, auditing, or moving files. The point is to see hierarchy clearly without flooding the context window or accidentally crawling dependency/build trash.

Default behavior is metadata-first. Do not read file contents unless the task needs classification details and the file is clearly safe to inspect.

## When to Use

Use this skill when:

- The user asks to see a folder tree, contents, subfolders, or files.
- The user asks to organize, sort, clean, map, classify, or triage a folder.
- A folder name is vague, e.g. `repos`, `projects`, `misc`, `old`, `backup`, `stuff`, `to review`.
- You need to understand whether a path is a project, a container, a dependency dump, a media folder, or junk.
- You need a compact tree artifact for later moves.

Do not use this for a single known file or when a shallow `search_files(target='files')` is already enough.

## Default Rules

1. **Resolve path intent first.**
   - On Xan's server, `~/Documents` usually means Windows Documents: `/mnt/c/Users/santi/Documents`.
   - If the user explicitly says WSL/Linux home, use `/home/xantastique/Documents` or the provided path.

2. **Bound the tree.**
   - Default depth: 4.
   - Default max entries per directory: 80.
   - Default max total entries: 2,000.
   - Increase only when the user asks or the tree is still ambiguous.

3. **Skip noise by default.**

```text
.git
node_modules
venv
.venv
__pycache__
.mypy_cache
.pytest_cache
.ruff_cache
.cache
.next
.nuxt
dist
build
coverage
.tox
.eggs
*.egg-info
vendor
third_party
models
checkpoints
Hermes/Artifacts
```

4. **Preserve sensitive material.**
   - For keys, vaults, credentials, backups, browser profiles, password stores, or token-looking paths, list names and metadata only.
   - Do not print secrets or read contents.

5. **Do not move/delete from the tree step.**
   - Tree inspection informs a plan.
   - Moves/deletions require a manifest and, for destructive actions, explicit approval.

## Recommended Python Tree Script

Use `execute_code` for 3+ calls or direct `terminal` for one-off checks. This script creates a compact tree and metadata summary without reading contents:

```python
from pathlib import Path
import os, json, time

root = Path('/path/to/root')
max_depth = 4
max_entries_per_dir = 80
max_total = 2000
skip_names = {
    '.git','node_modules','venv','.venv','__pycache__','.mypy_cache','.pytest_cache',
    '.ruff_cache','.cache','.next','.nuxt','dist','build','coverage','.tox','.eggs',
    'vendor','third_party','models','checkpoints'
}

rows = []
truncated = []
counts = {'dirs': 0, 'files': 0, 'bytes': 0, 'skipped_dirs': 0}

def safe_stat(p):
    try:
        return p.stat()
    except OSError:
        return None

def walk(p, depth=0):
    if len(rows) >= max_total:
        truncated.append(f'max_total reached at {p}')
        return
    st = safe_stat(p)
    if st is None:
        rows.append({'depth': depth, 'type': 'error', 'path': str(p), 'name': p.name})
        return
    if p.is_dir():
        counts['dirs'] += 1
        if depth >= max_depth:
            rows.append({'depth': depth, 'type': 'dir', 'path': str(p), 'name': p.name, 'truncated': 'max_depth'})
            return
        try:
            children = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except OSError:
            rows.append({'depth': depth, 'type': 'error', 'path': str(p), 'name': p.name})
            return
        shown = 0
        for child in children:
            if child.name in skip_names or child.name.endswith('.egg-info'):
                counts['skipped_dirs'] += int(child.is_dir())
                continue
            if shown >= max_entries_per_dir:
                truncated.append(f'max_entries_per_dir reached in {p}')
                break
            walk(child, depth + 1)
            shown += 1
    else:
        counts['files'] += 1
        counts['bytes'] += st.st_size
        rows.append({'depth': depth, 'type': 'file', 'path': str(p), 'name': p.name, 'bytes': st.st_size, 'mtime': st.st_mtime})

walk(root, 0)
print(json.dumps({'root': str(root), 'counts': counts, 'truncated': truncated, 'rows': rows}, indent=2))
```

## Project Classification Hints

When mapping scattered project folders, use marker files **plus** extension dominance and sample paths. Marker files are evidence, not verdicts.

- Python: `pyproject.toml`, `setup.py`, `requirements.txt`, `Pipfile`, `poetry.lock`, `*.py`
- JavaScript/TypeScript: `package.json`, `tsconfig.json`, `vite.config.*`, `next.config.*`, `*.js`, `*.ts`, `*.tsx`
- Dart/Flutter: `pubspec.yaml`, `lib/*.dart`, `android/`, `ios/`
- Rust: `Cargo.toml`, `src/main.rs`, `src/lib.rs`
- Go: `go.mod`, `*.go`
- .NET: `*.csproj`, `*.fsproj`, C#-dominant source, SDK-style project files
- Java/Kotlin: `pom.xml`, `build.gradle`, `*.kt`, `*.java`
- C/C++: `CMakeLists.txt`, `Makefile`, `*.c`, `*.cpp`, `*.h`, `*.hpp`, `*.vcxproj`, `*.filters`, C/C++-dominant Visual Studio solutions
- Data/notebooks: `*.ipynb`, `*.csv`, `*.parquet`, `notebooks/`, `data/`
- Docs: mostly `*.md`, `docs/`, no code markers

Classification cautions:

- `requirements.txt` inside a native/C++ project can be tooling or a sidecar; do not classify as Python if `.cpp/.h/CMake/vcxproj` dominate.
- `.sln` is not automatically .NET. Visual Studio C++ projects commonly use `.sln`; inspect `.vcxproj`, `.filters`, and source extensions.
- Full-stack repos with backend + frontend markers may belong under the primary runtime or `Source/Unknown_Mixed`; state the assumption.
- Containers named `repos`, `projects`, `old`, `misc`, or `archive` are not projects by name alone. Inspect one level deeper.

## Output Shape

For chat, keep it compact:

```text
Tree scan:
- Root: ...
- Depth: ...
- Entries: ...
- Skipped: ...
- Truncated: yes/no

Likely buckets:
- Source/Python: ...
- Source/JavaScript_TypeScript: ...
- Source/Unknown_Mixed: ...
- To_Review: ...

Artifact:
- Windows -> ...
- WSL -> ...
```

For durable artifacts, save:

```text
FileTree.json
FileTree.txt
ClassificationPlan.md
```

If an automated classifier needed manual correction, also save:

```text
RefinedMoveMap.md
```

Reference examples:

- `references/2026-05-22-repos-classification-windows-tree.md` — lessons from classifying a misplaced mixed `repos` folder under Windows Documents.

## Common Pitfalls

1. **Crawling dependencies.** Always exclude dependency/build folders unless the dependency folder itself is the suspected misplaced item.
2. **Assuming parent folder language.** A folder under `Source/Python` can contain JS, Dart, Rust, docs, or nested unrelated projects.
3. **Treating generated folders as projects.** `node_modules`, `.venv`, `dist`, and `build` are evidence of a project nearby, not projects themselves.
4. **Overprinting huge trees.** Put the complete tree in an artifact; summarize in chat.
5. **Path breakage.** Moving source projects can break IDE workspaces, venvs, scripts, shortcuts, and git remotes. Produce a dry-run map first.
6. **Missing nested repos.** Check for nested `.git` directories, but don't descend into `.git` internals.
7. **Marker-file tunnel vision.** `requirements.txt` does not override a C/C++-dominant tree; `.sln` does not automatically mean .NET. Use extension dominance and sample paths before assigning buckets.
8. **WSL-over-Windows scan drag.** Large `/mnt/c` tree walks from Python may time out. For Windows-host folders, use a bounded PowerShell scanner when WSL traversal becomes slow.
9. **Case-near sibling folders.** `repos` and `Repos` under the same Windows parent are operationally dangerous. Inspect both before merging or moving.

## Verification Checklist

- [ ] Correct root resolved, especially Windows vs WSL Documents.
- [ ] Depth and skip rules stated.
- [ ] Tree artifact saved if output is large.
- [ ] Classification uses markers, not folder names alone.
- [ ] Uncertain cases marked review-required.
- [ ] No file moves/deletions performed during inspection.
