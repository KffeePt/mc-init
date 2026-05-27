# 2026-05-26 Agent self-documentation and reproduction bundles

## Context

Xan asked Wilson to produce a full recursive self-documentation bundle to reproduce Wilson as a new agent named `emma`. The result was a constructor-facing packet, not just a summary: identity map, skills/plugins, gateway architecture, memory/artifacts, init/bootstrap, comms protocols, implicit behaviors, known gaps, reproduction checklist, raw self-model, raw inventories, copied core skill files, sanitized config, and QA artifacts.

## Class-level pattern

Use this when creating or updating agents, forks, child agents, or constructor packets.

### Required sections

1. Identity + role map.
2. Skill/plugin inventory.
3. Plugin/gateway architecture.
4. Memory + artifact system.
5. Init/bootstrap sequence.
6. Communication protocols.
7. Implicit behaviors + learned patterns.
8. Known gaps + upgrade notes.
9. Reproduction checklist.
10. Raw self-model.

### Supporting sub-artifacts

Recommended bundle contents:

```text
Manifest.md
QA Report.json
Bundle SHA256.txt
Config Template Sanitized.md
Source Tree Snapshot.md
raw/
  command_outputs.json
  config.sanitized.yaml
  env.keys.txt
  skills_inventory.json
  plugins_inventory.json
  hermes_documents_tree_bounded.txt
  init_zip_inventory.json
  *.schema_counts.json
  agent-comms.sh.snapshot.txt
  agent-self-update-protocol.md.snapshot.txt
sub-artifacts/
  core-skill-files/
  AGENTS.local.md
  STATE.template.md
```

Include current `STATE.md` only if useful and reviewed; it can be verbose. Never include secrets.

## Redaction boundary

Include:
- skill files and metadata;
- sanitized config;
- env var names only;
- source/workspace tree snapshots;
- protocol/comms snapshots;
- DB schema/counts;
- operating guides and templates.

Exclude:
- raw `.env` values;
- private keys;
- auth stores/tokens;
- browser profiles/cookies;
- raw transcript dumps;
- full logs;
- credential vaults.

## Authority and fork warning

A fork is not reproduced by copying `config.yaml`. Constructor packets must carry the layered behavior:

1. prompt/persona;
2. durable memory seeds;
3. skills;
4. artifact workspace;
5. gateway/platform config;
6. TTS behavior;
7. STATE ledger;
8. multi-agent authority protocol;
9. QA routine;
10. approval/refusal boundaries.

If a behavior came from current injected instructions rather than files, explicitly document it. Context is not inheritance.

## QA expectations

Run `omni-qa` before delivery:

- verify required section files exist;
- verify raw inventories exist;
- verify core skill sub-artifacts exist;
- verify ZIP exists/nonzero;
- run a refined secret-pattern scan and manually review hits;
- write hash file;
- update `STATE.md`.

Do not claim the fork works until the fork is actually built and runs its first-live-response QA gate.