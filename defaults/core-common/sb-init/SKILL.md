---
name: sb-init
description: Use when initializing, updating, or operating a subordinate Hermes/OpenClaw-style agent that receives authority from mc-init and stores local drawer state on its own remote branch.
version: 1.0.0
author: Wilson / Hermes Agent
license: MIT
platforms: [windows, wsl, linux]
metadata:
  hermes:
    tags: [subordinate, init, drawer, bootstrap, remote-state, agent-comms]
    related_skills: [mc-init, meta-gateway, orchestration, git-gh]
---

# SB-Init — Subordinate Bootstrap Init

## Overview

`sb-init` is the subordinate-safe counterpart to `mc-init`. It is for agents that are managed by the controller but must still initialize, update, sync status, and communicate when direct network access is unavailable.

Subordinates use the `mc-init` repository as the source of truth, but they do not receive controller authority. Their mutable state lives in the shared `drawer` repo on a branch owned by that subordinate identity.

## When to Use

Use this skill when:

- Initializing Arby/LilJon or another subordinate agent.
- Registering a subordinate drawer branch.
- Applying an `init.zip` produced by `mc-init`.
- Syncing subordinate Desktop/Hermes state to remote drawer.
- Processing drawer `Inbox/` and `Outbox/` messages.
- Handling a drawer sync conflict.
- Updating subordinate default skills from the controller package.

Do not use this for controller-only work. Use `mc-init` on the controller.

## Identity Contract

Each subordinate needs:

```yaml
schema: hermes.drawer.agent.v1
role: subordinate
agent_id: arby-liljon
computer_label: koffeelap
branch: drawer/arby-liljon/arby-liljon-koffeelap
controller_branch: main
repo: git@github.com:KffeePt/drawer.git
```

Branch format:

```text
drawer/<group>/<agent-name>-<computer-label>
```

Use lowercase, digits, hyphens, and slashes. No spaces.

## Bootstrap Steps

1. Verify GitHub/SSH auth and controller trust material.
2. Clone or update `mc-init` read-only.
3. Clone or initialize `drawer`.
4. Create/switch to the subordinate branch.
5. Write `.drawer/agent.yaml`, `.drawer/branch.yaml`, and `Hermes/source-map.yaml`.
6. Install default skills from the `mc-init` package.
7. Set up scheduled safe sync.
8. Send first status envelope to controller through `Outbox/`.

## Safe Sync Algorithm

Scheduled sync must never hard-reset or force-push.

```text
lock -> fetch -> commit local checkpoint -> rebase branch -> push branch -> push checkpoint tag -> unlock
```

If the remote branch does not exist yet, first push creates it.

## Conflict Stall Policy

On conflict or remote failure:

1. Abort rebase if active.
2. Write `.drawer/conflict.json`.
3. Pause/disable the scheduled sync task.
4. Write a notification envelope in `Outbox/`.
5. If controller notification is available, notify Telegram first and email second.
6. Wait for human/controller resolution.

Never auto-resolve scripts, config, source maps, skills, schema files, or inbox/outbox identity collisions.

## Drawer Message Handling

Incoming messages live under `Inbox/`. Outgoing messages live under `Outbox/`.

Message schema:

```json
{
  "schema": "hermes.drawer.message.v1",
  "message_id": "uuid",
  "from": "controller:wilson-controller",
  "to": "agent:arby-liljon:koffeelap",
  "created_at": "2026-05-30T00:00:00Z",
  "ttl_seconds": 86400,
  "requires_ack": true,
  "kind": "command|status|artifact-request|artifact-ready|scp-plan|ack|conflict",
  "body": {},
  "signature": "ssh-signature-or-minisign"
}
```

Reject expired, unsigned, malformed, or wrong-recipient messages.

## Security Rules

- Do not write to drawer `main`.
- Do not push to `mc-init`.
- Do not store private keys, tokens, cookies, raw `.env`, Plex tokens, qBittorrent credentials, or browser profiles in drawer.
- Large artifacts should move by SCP/direct transfer when possible; Git drawer carries manifests and coordination, not bulk payloads.
- Sensitive actions require explicit confirmation or controller-signed command policy.

## Verification Checklist

- [ ] `agent_id`, `computer_label`, and branch are correct.
- [ ] Drawer remote points to `git@github.com:KffeePt/drawer.git`.
- [ ] Current branch is not `main` for subordinate agents.
- [ ] `.drawer/agent.yaml` exists and role is `subordinate`.
- [ ] Scheduled sync creates checkpoint tags and pushes only the subordinate branch.
- [ ] Conflict test stalls rather than auto-resolving.
- [ ] No secrets are present in drawer tracked files.
- [ ] `mc-init` package hash verified before applying updates.
