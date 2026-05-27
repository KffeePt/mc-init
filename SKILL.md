---
name: mc-init
description: "Master Controller Init — central management for Hermes agent initialization. Manages current and past init package versions, default skills, build/publish scripts, agent-to-agent protocol/contract, and the default skill roadmap. Canonical source for all child-agent bootstrap operations."
version: 1.0.0
author: Wilson / Hermes Agent
license: MIT
platforms: [windows, wsl, linux]
metadata:
  hermes:
    tags: [init, bootstrap, mc-init, controller, agent-setup, child-node, skills-management]
    related_skills: [meta-gateway, orchestration, git-gh, storage-explorer]
---

# MC-Init — Master Controller Init System

## Overview

The central init management system for Xan's Hermes agent ecosystem. Lives at `~/Documents/Hermes/Init/` and is version-controlled via the `mc-init` remote repository.

This is the **single source of truth** for:
- Child-agent bootstrap packages (`init.zip`)
- Default core-common skills
- Agent-to-agent protocol and contracts
- Init build and publish scripts
- Default skill roadmap

## Directory Structure

```
Hermes/Init/                    # mc-init repo root
├── SKILL.md                    # This file
├── ROADMAP.md                  # Default skill roadmap
├── README.md                   # Repo overview
├── init_prompt.md              # Bootstrap prompt for child agents
├── init.py                     # Initializer CLI entrypoint
├── src/laptop_init/            # Python source for init tool
├── defaults/core-common/       # Default child-safe skills
│   ├── file-organization/
│   ├── get-artifact/
│   ├── git-gh/
│   ├── image-gen/
│   ├── meta-gateway/
│   ├── omni-qa/
│   ├── orchestration/
│   ├── plan-mode/
│   └── storage-explorer/
├── scripts/                    # Build/publish scripts
│   ├── build-init.sh           # Build init.zip from current state
│   └── publish-init.sh         # Publish init.zip to child agents
├── protocol/                   # Agent-to-agent protocol
│   ├── Agent Message Contract.md
│   ├── sync_policy.yaml
│   └── meta-gateway-protocol.md
├── seeds/                      # Child agent seed files
│   ├── SOUL.md
│   ├── xan_preferences.md
│   └── sync_policy.yaml
├── controllers/                # Controller auth material
│   └── lazarus_allowed_signers
├── docs/                       # Controller documentation
│   └── controller_policy.md
└── versions/                   # Version tracking
    ├── current/                # Current init.zip + manifest
    └── archive/                # Archived versions
```

## When to Use

Use this skill when Xan asks to:

- Build or update the init bootstrap package
- Add/remove default child-safe skills
- Update the agent-to-agent protocol or contract
- Manage init package versions
- Publish init updates to child agents
- Review or modify the default skill roadmap
- Initialize a new child agent

## Building init.zip

```bash
cd ~/Documents/Hermes/Init
bash scripts/build-init.sh [version_tag]
```

This produces `versions/current/init.zip` with all default skills, seeds, protocol files, controller material, and the bootstrap prompt.

## Publishing to Child Agents

```bash
cd ~/Documents/Hermes/Init
bash scripts/publish-init.sh arby
```

This:
1. Builds the latest init.zip
2. Archives the previous version
3. SCPs init.zip to the target child agent
4. Sends a coordination message via the agent comms layer
5. Updates the version manifest

## Default Skills

The following skills are included in every child-agent bootstrap by default:

| Skill | Category | Purpose |
|---|---|---|
| `file-organization` | Productivity | Safe file/folder organization and cleanup |
| `get-artifact` | Productivity | Artifact retrieval and delivery |
| `git-gh` | Software Dev | Git + GitHub CLI operations |
| `image-gen` | Creative | Image generation and editing |
| `meta-gateway` | Multi-Agent | Agent hierarchy and comms routing |
| `omni-qa` | Software Dev | Universal QA pass framework |
| `orchestration` | Multi-Agent | Work routing across agents |
| `plan-mode` | Software Dev | Plan-before-execute workflow |
| `storage-explorer` | Productivity | Omni-utility storage management |

## Version Management

Current version is stored in `versions/current/` alongside its manifest:
- `versions/current/init.zip` — latest build
- `versions/current/manifest.json` — contents, hashes, timestamps

Past versions are archived in `versions/archive/YYYY-MM-DD/` with the same structure.

## Remote Repository

```
https://github.com/<user>/mc-init
```

Pushing updates:
```bash
cd ~/Documents/Hermes/Init
git add -A
git commit -m "update: <description>"
git push origin main
```

## Security

- `init.zip` may contain the controller's **public** SSH key only
- `init_res.zip` may report public key presence/fingerprints, never private keys
- Neither archive may contain: private keys, raw `.env`, API tokens, cookies, browser profiles, credential vaults, or raw memory dumps
- Controller update signatures use `ssh-keygen -Y sign/verify`
- The init skill authority stays on the controller machine only — child agents receive only `core-common` skills

## Verification Checklist

- [ ] All default skills are present in `defaults/core-common/`
- [ ] `init_prompt.md` is up to date with current protocol
- [ ] `init.py` compiles cleanly
- [ ] `controllers/lazarus_allowed_signers` contains current controller public key
- [ ] `build-init.sh` produces valid init.zip
- [ ] `publish-init.sh` SCPs correctly to target
- [ ] No secrets in `seeds/`, `defaults/`, or `versions/`
- [ ] Git remote `mc-init` is configured and reachable
- [ ] `ROADMAP.md` reflects current priorities
