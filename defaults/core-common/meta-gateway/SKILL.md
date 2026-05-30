---
name: meta-gateway
description: Use when coordinating multiple local agents/machines so SSH, SCP, command execution, registry updates, file transfer requests, and communication state pass through a controlled hierarchy with Wilson/Lazarus as main controller.
version: 1.0.0
author: Wilson / Hermes Agent
license: MIT
platforms: [windows, wsl, linux]
metadata:
  hermes:
    tags: [multi-agent, gateway, ssh, scp, hierarchy, registry, controller, tailscale]
    related_skills: [hermes-agent, orchestration, storage-explorer, file-organization, omni-qa, git-gh, mc-init, tailscale-homelan]
---

# Meta-Gateway

## Overview

The meta-gateway is the control plane for Xan's multi-agent system. It is not just “SSH works.” That is plumbing. The gateway defines who may ask whom to do what, how command/file-transfer requests are represented, how registry updates move, and where authority stops.

Hierarchy:

```text
Xan
  -> Wilson / Lazarus  = main controller, final authority, registry owner
      -> Arby / LilJon = subordinate child machine / worker
      -> future agents = subordinate workers unless explicitly promoted
```

All SSH, SCP, command execution, file transfer, registry updates, and communication-status changes must be routed through this hierarchy or explicitly approved by Xan.

## Notification / Remote Action Layer

Wilson/Lazarus may initiate scoped remote action requests to Arby/LilJon and future subordinate Hermes agents. The subordinate executes only the stated non-destructive or already-approved scope, then reports status, artifacts, blockers, and verification back through the controller so Xan sees the work in Telegram. This prevents subordinate work from becoming headless.

### Control Channel (Auto-Execute)

For init updates, system config changes, and service control, Wilson sends messages with `"channel": "control"` to Arby's inbox. These are auto-processed by the `control-channel-watcher` systemd service running on Arby/LilJon.

Control channel messages:
- Require `"channel": "control"` field
- Must pass verification (origin, approval_source, secrets_policy, required fields)
- Auto-trigger: init.zip extraction, `init.py approved-init`, skill verification, service restart
- Results are logged to journal and queued as `control_result_*.json` in comms_pending

Regular comms messages (no `channel` field or `channel: "comms"`) are routed to `comms_pending/` for the agent to read manually. The watcher never auto-executes comms messages.

Flow:

1. Wilson/Lazarus creates a request envelope with `"channel": "control"` and exact scope.
2. Wilson sends via SCP/SSH to Arby's Windows inbox at `C:\Users\santi\Documents\Hermes\Comms\arby\inbox\`.
3. The control-channel-watcher picks it up within 15 seconds.
4. Watcher verifies the message, executes allowed actions, logs results.
5. Results and notifications are queued for the Hermes agent to relay to Xan via Telegram.

Allowed without fresh approval when covered by existing setup policy: status checks, diagnostics, non-destructive verification, artifact creation, init/update application, and file-transfer tests. Still approval-gated: destructive actions, credential export, private-key transfer, raw env transfer, browser profile transfer, public firewall exposure, and persistence/autostart changes.

## When to Use

Use this skill when:

- setting up or updating child agents;
- sending commands from Wilson/Lazarus to Arby/LilJon or another subordinate;
- transferring files with SCP/SFTP/rsync/Tailscale Taildrop;
- asking a subordinate to run a local command, inspect state, or create an artifact;
- updating agent registries, machine registries, drive/path registries, service registries, or communication maps;
- deciding whether an agent has authority to perform an action;
- reviewing reports from `init_res.zip` or child-agent handoffs.

## Authority Model

Roles:

- **Xan:** human owner. Can override anything with explicit instruction.
- **Wilson/Lazarus:** main controller. Owns final review, shared memory, shared skills, shared registries, and init/update authority.
- **Subordinate agents:** local observation and execution within approved scope. They may propose registry updates and request commands/transfers; they do not overwrite controller state.

Controller-only authority:

- reusable init/bootstrap skills;
- shared-memory edits;
- shared registry canonical writes;
- promotion of local-adapted skills to common skills;
- signed controller updates;
- destructive or security-sensitive orchestration decisions.

Subordinate-allowed authority:

- local observation;
- local verification;
- local artifact creation;
- scoped setup commands approved by init/update policy;
- sending candidate reports and proposed registry patches.

## Gateway Rule

All cross-agent operations use a request envelope. Do not send vague orders.

Required fields:

```yaml
request_id: <stable timestamp or uuid>
origin_agent: <agent/body/machine>
target_agent: <agent/body/machine>
operation_type: command | file_transfer | registry_update | status_report | artifact_handoff | remote_action_request | telegram_status_report | qa_report
intent: <why this is needed>
scope: <exact paths/services/commands/registries allowed>
risk_level: low | medium | high
approval_source: xan | controller_signed_update | existing_policy | needs_approval
expected_output: <what proves success>
rollback_or_stop_condition: <when to stop>
secrets_policy: no_secrets | public_keys_only | explicit_secret_approval_required
```

If the request lacks these fields, ask for/derive them before executing. Sloppy envelopes become accidents. Accidents become folklore.

## Command Execution Policy

Allowed without fresh approval when already covered by init/setup policy:

- SSH connectivity tests;
- local status checks;
- registry/situational-awareness collection;
- non-destructive artifact creation;
- installing child-safe seed files during approved init;
- implanting Lazarus's **public** SSH key during approved init.

Requires explicit Xan approval:

- destructive commands;
- public firewall exposure;
- persistence/autostart changes outside approved init;
- credential export;
- private-key transfer;
- raw `.env` export;
- browser profile/cookie transfer;
- broad recursive deletion/move operations;
- subordinate overwriting controller registries directly.

Subordinates may request high-risk actions, but Wilson/Lazarus must review and Xan must approve where required.

## File Transfer Policy

Allowed transfer types:

- init packages: `init.zip`;
- return bundles: `init_res.zip`;
- logs/reports/artifacts;
- signed controller update manifests/signatures;
- public SSH keys and fingerprints;
- scoped helper scripts intended for the child.

Forbidden without explicit Xan approval:

- private keys;
- API tokens/secrets;
- raw `.env` files;
- browser profiles/cookies;
- credential vaults;
- bulk personal data dumps.

File transfer request must include source, destination, purpose, overwrite expectation, and verification command.

## Registry Update Flow

Subordinate registries are candidate input, not canonical truth.

Flow:

1. Subordinate collects local facts into JSON registry files.
2. Subordinate sends report or `init_res.zip` to Xan/Lazarus.
3. Wilson/Lazarus validates freshness, identity, and scope.
4. Wilson/Lazarus imports compact durable facts into canonical registry/memory/state.
5. Conflicts resolve in favor of Wilson/Lazarus unless Xan says otherwise.

Registry classes:

- `agent_registry.json`
- `machine_registry.json`
- `drive_registry.json`
- `path_registry.json`
- `program_registry.json`
- `service_registry.json`
- `comms_registry.json`
- `remote_action_registry.json`

## Init Integration

Every `init.zip` sent to a child agent should include this skill as a child-safe common skill. Init packages are built and published from the central `mc-init` system at `~/Documents/Hermes/Init/` (repo: `https://github.com/KffeePt/mc-init`).

Build: `bash scripts/build-init.sh [version_tag]` — produces `versions/current/init.zip`.
Publish: `bash scripts/publish-init.sh arby [version_tag]` — builds, SCPs, verifies hash, and sends a JSON coordination envelope to Arby's inbox.

Fresh-agent flow:

1. Agent receives `init.zip`.
2. User says: `read init_prompt.md and do whatever it says.`
3. Agent reads `init_prompt.md`.
4. Agent loads/uses `meta-gateway` to understand hierarchy and routing.
5. Agent transplants child-safe skills/preferences/scripts/plugin notes/shared memory seeds.
6. Agent runs or requests admin `init.py` to implant Lazarus's public SSH key.
7. Agent verifies SSH/Tailscale/comms.
8. Agent maps situational awareness.
9. Agent returns `init_res.zip` to Xan/Lazarus.

## Verification Checklist

- [ ] Wilson/Lazarus identified as main controller.
- [ ] Target subordinate identified by agent/body/hostname/Tailscale IP.
- [ ] Operation envelope has all required fields.
- [ ] Risk level and approval source are correct.
- [ ] No private keys/secrets are included.
- [ ] File transfers have source/destination/purpose/overwrite/verification.
- [ ] Registry updates are candidate reports, not blind canonical writes.
- [ ] Results include observed facts, actions taken, verification, risks, and remaining work.
