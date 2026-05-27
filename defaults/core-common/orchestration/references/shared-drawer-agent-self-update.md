# Shared Drawer Agent Self-Update Protocol

## Purpose

Use this reference when maintaining a small local fleet of Hermes-style agents where one controller reviews updates from child machines. It encodes the Lazarus/LilJon arrangement without making every child a bootstrap authority.

## Current bodies

- `Lazarus` — Wilson's body, main controller, owns review/promotion/init authority.
- `LilJon` — Arby's body, laptop child node, owns local observation and local-adapted skills.

## Canonical exchange path

Windows:

```text
C:\Users\santi\Documents\Hermes\Shared Drawer\
```

WSL:

```text
/mnt/c/Users/santi/Documents/Hermes/Shared Drawer/
```

Recommended live files:

```text
Shared Drawer/
  Protocols/
    agent-self-update-protocol.md
    agent_shared_update.py
  Manifests/
    sync-policy.yaml
    agent-registry.yaml
  Incoming/<AgentName>/
  Outgoing/<AgentName>/
  Bundles/
  Reviews/
```

## Core rule

No blind bidirectional sync.

Child agents submit candidates; Lazarus reviews and promotes/rejects. Memory, SOUL, and shared skills are too sharp to let an unattended laptop overwrite controller doctrine.

## Candidate classes

### memory

Stable facts only:

- durable machine names/IPs
- stable service topology
- durable user preferences
- stable path conventions

Not allowed:

- temporary task state
- raw chat logs
- secrets
- current progress snapshots

### soul

Behavior/protocol/personality changes. Must be patch-style and controller-reviewed.

### skill

Repeatable workflow. Classify as:

- `core-common`
- `comms`
- `local-adapted`
- `private`
- `init`

`init` remains Lazarus/controller-only by default.

### bundle

Multi-file update with manifest and verification summary.

## Minimal review cycle

1. Child writes candidate under `Shared Drawer/Incoming/<AgentName>/`.
2. Child reports using the Agent Message Contract.
3. Lazarus checks for secrets, machine-specific assumptions, unsafe commands, and generality.
4. Lazarus accepts, rewrites, rejects, or marks needs-redaction.
5. Lazarus records result in STATE.md and/or `Shared Drawer/Reviews/`.
6. If accepted, Lazarus publishes shared update under `Shared Drawer/Outgoing/Lazarus/`.

## Forbidden sync content

- raw `.env` files
- private keys
- tokens/cookies
- browser profiles
- raw memory dumps
- another machine's private skills
- child-overwrites-controller state

## Helper script pattern

The helper script `agent_shared_update.py` should create candidate folders only. It should not apply updates directly. Application remains a reviewed controller action.

Example:

```bash
python3 ".../Shared Drawer/Protocols/agent_shared_update.py" \
  --agent LilJon \
  --kind skill \
  --title "windows ssh admin key repair" \
  path/to/evidence.md
```

## Verification standard

Every accepted update needs:

- files changed
- commands run
- parse/lint/test result if code or YAML
- rollback path if risky
- remaining risks

If there is no verification, there is no promotion. That is not bureaucracy. That is how you avoid teaching the fleet superstition.
