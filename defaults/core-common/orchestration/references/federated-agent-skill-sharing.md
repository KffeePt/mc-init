# Federated Agent Skill Sharing

## Context

Use this reference when designing or bootstrapping multiple local Hermes agents across Xan's machines. The desired shape is not one globally synced hive. Each agent should adapt to its local machine while importing only common policy, init, and communication knowledge from the controller.

## Hierarchy

### Tier 0 — User policy layer

Portable user-level doctrine and defaults:

- generic `SOUL.md` traits, without fictional-character/persona-specific references
- Xan response/style/workflow preferences
- plan-mode behavior
- artifact delivery conventions
- safety posture

This layer is shared, compact, and contains no secrets.

### Tier 1 — Controller agent

Primary Hermes instance on `Lazarus`, Wilson's body / main server.

Responsibilities:

- orchestration and final judgment
- deciding which skills are promoted from local to shared
- verifying child-agent work
- owning shared init/comms/common bundles
- enforcing boundaries around secrets and local/private skill export

### Tier 2 — Machine/site agents

Agents on a laptop, Windows host, WSL distro, media server, or other durable machine. Current child machine: `LilJon`, Arby's body, hostname `desktop-mca3em3`.

Responsibilities:

- local diagnostics and local operations
- local tool/service discovery
- machine-specific skill growth
- reporting candidate common knowledge to controller

These agents may import shared seed files but should keep local-adapted and private skills local by default.

### Tier 3 — Ephemeral workers

One-shot workers such as temporary Hermes CLI runs, Codex/Gemini/OpenCode lanes, or bounded subagents.

Responsibilities:

- execute a narrow task
- report facts, changed files, verification, and risks
- avoid durable memory unless explicitly instructed

## Skill classes

- `core-common`: portable style, safety, plan-mode, artifact delivery, generic operating traits.
- `init`: bootstrap and setup procedures, such as SSH, Tailscale checks, Hermes install/profile setup.
- `comms`: inter-agent message contracts, SSH delegation wrappers, artifact transfer, heartbeat/status formats.
- `local-adapted`: machine-specific local learning. Never globally synced automatically.
- `private`: sensitive or identity-bound procedures. Never exported automatically.

## Promotion flow

1. Child agent creates or patches a local skill.
2. Child marks it as `local-adapted`, `private`, `candidate-common`, `candidate-init`, or `candidate-comms`.
3. Child reports the candidate to the controller using a structured report.
4. Controller reviews for secrets, machine-specific assumptions, stale paths, unsafe commands, and cross-agent value.
5. Controller promotes, rewrites into generic form, leaves local, or rejects.

## Message contract for child agents

Require child agents to report:

```md
## Result
- Success / partial / blocked / failed

## Observed Facts
- Facts verified by tools or local files

## Actions Taken
- Commands, files changed, services touched

## Files / Artifacts
- Paths created/changed

## Verification
- Checks run and results

## Risks / Assumptions
- What might be wrong or unverified

## Proposed Skill Promotions
- Local skills that may deserve promotion to common/init/comms

## Remaining Work
- What needs controller/human action
```

## Bootstrap seed files

A child-agent bootstrap bundle should usually include:

- `SOUL.md` — generic traits and operating discipline; no Wilson-specific fictional-character references.
- `Xan Preference Seed.md` — compact user/workflow/delivery preferences.
- `plan-mode/SKILL.md` — copied local plan-mode skill.
- `sync_policy.yaml` — explicit common/init/comms/local/private rules.
- `agent_message_contract.md` — report format.
- init scripts, such as SSH/Hermes/Tailscale bootstrap.

## SSH/key bootstrap rule

If Xan explicitly chooses full automation, `authorized_keys` may be replaced rather than marked-block appended. Even then:

- back up the existing `authorized_keys` first
- replace with the controller key only
- fix permissions/ACLs
- restart SSH
- print rollback/verification commands

This is convenient but carries lockout risk if old keys mattered. Treat it as a sharp tool, not a lifestyle.

## Sync mechanics

Prefer explicit import/export bundles over continuous global sync. The canonical exchange path is:

```text
C:\Users\santi\Documents\Hermes\Shared Drawer\
```

The live protocol is stored at:

```text
C:\Users\santi\Documents\Hermes\Shared Drawer\Protocols\agent-self-update-protocol.md
```

Agents submit memory/SOUL/skill/bundle candidates under `Shared Drawer/Incoming/<AgentName>/`; Lazarus reviews, accepts/rejects/redacts, and publishes accepted controller-owned updates under `Shared Drawer/Outgoing/Lazarus/`. No blind two-way sync.

Shared bundle shape:

```text
HermesShared/
  core-common/
    SOUL.md
    Xan Preference Seed.md
    skills/
      plan-mode/SKILL.md
  init/
    bootstrap scripts
  comms/
    agent_message_contract.md
    ssh_delegation_wrapper.md
  manifests/
    sync_policy.yaml
```

Child overlay shape:

```text
~/.hermes/
  SOUL.md
  skills/
    core-common/
    init/
    comms/
    local-adapted/
    private/
```

Controller wins conflicts in shared/common skills. Child wins local skills. Private skills never sync.

## Command execution and file transfer

Xan has authorized command execution and file transfer between `Lazarus` and subordinate agents when scoped to setup, verification, artifact handoff, logs/reports, Shared Drawer sync, or explicit user-requested operations. Subordinate requests from `LilJon`/Arby are allowed when source and scope are clear.

Still require explicit Xan approval for destructive commands, credential export, private key transfer, raw `.env` transfer, browser profile transfer, firewall/public-exposure changes, or persistence/autostart changes.

## init_res.zip return bundles and situational awareness

LilJon/Arby init runs must return `init_res.zip` to Xan/Lazarus after bootstrap. The bundle should contain `situational_awareness.json`, `windows_verify.txt`, and `controller_ingest.md`.

Programmatic situational awareness means concrete subordinate-only state: drive roots/capacity/free space, bounded path maps, content-type distributions, installed program inventory, JSON registries for agent/machine/drive/path/program/service state, SSH/Tailscale/service/network state, and machine identity. It does not mean prose summaries, vibes, or raw memory dumps.

Lazarus ingests returned bundles with:

```bash
python3 "/mnt/c/Users/santi/Documents/Hermes/Shared Drawer/Protocols/ingest_liljon_init_res.py" /path/to/init_res.zip
```

Only compact reviewed facts from the generated `memory_candidate.md` should be saved to durable memory.
