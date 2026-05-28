---
name: orchestration
description: "Use when routing work across multiple coding/AI agents such as Antigravity, Cursor Composer, Gemini CLI, Codex fallback, OpenCode, and Hermes subagents with model-tier selection."
version: 1.0.0
author: Wilson / Hermes Agent
license: MIT
platforms: [windows, wsl, linux]
metadata:
  hermes:
    tags: [orchestration, agents, antigravity, cursor, gemini, codex, delegation, model-routing]
    related_skills: [hermes-agent, codex, opencode, autonomous-ai-agents]
---

# Orchestration

## Overview

Use this skill to act as an orchestrator over multiple agent backends and model tiers. Hermes remains the controller: it plans, routes, monitors, verifies, and reports. External agents are workers, not authorities.

Target worker stack on Xan's Windows/WSL host:

- Antigravity desktop/CLI launcher on Windows
- Cursor CLI / Composer when available
- Gemini CLI for lightweight or medium autonomous tasks
- Codex CLI as fallback when installed/authenticated
- OpenCode when installed/authenticated
- Hermes `delegate_task` subagents for bounded internal research/review lanes
- Direct Hermes tools for file/terminal/browser work when a worker would add overhead

This skill is intentionally model-name configurable. Model names drift. Vendors love renaming things. A quiet little taxonomy fire.

Current user-facing routing policy should live in:

```text
C:\Users\santi\Documents\Hermes\Config\ModelRouting.yaml
```

The skill template `templates/model-routing.yaml` is a starter/reference shape; the workspace config is the editable operational copy.

## Default Model Tiers

Treat these as defaults, not hardcoded law. If the user's config has newer model names, use the updated names and note the substitution.

| Tier | Default model target | Use for |
| --- | --- | --- |
| simple | Gemini 3.5 Flash | summarization, classification, simple edits, fast checks, extraction, low-risk scaffolding |
| medium | Gemini 3.1 Pro | moderate debugging, multi-file review, refactors with low blast radius, docs-to-code translation |
| maximum | GPT-5.5 | hard debugging, architecture decisions, security-sensitive changes, complex synthesis, final arbitration |
| planning | Claude Opus 4.6/4.7 | high-level plans, decomposition, risk analysis, design review, strategy |

If exact model aliases are unknown, discover first:

```bash
hermes model
hermes config
hermes config path
```

For CLI workers, probe their own model syntax:

```bash
gemini --help
codex --help
opencode --help
cursor --help
powershell.exe -NoProfile -Command "& 'C:\\Users\\santi\\AppData\\Local\\Programs\\Antigravity\\bin\\antigravity.cmd' --help"
```

## Routing Policy

1. **Understand and plan first.** For multi-step or file/system-changing work, show Xan a concise plan summary unless he says `skip plan`.
2. **Choose the smallest competent worker.** Do not burn maximum-tier models on trivial work.
3. **Use external agents for bounded lanes.** Give each worker a narrow task, expected output, allowed paths, and verification criteria.
4. **Keep Hermes as arbiter.** Read back diffs/logs/tests yourself before claiming success.
5. **Use worktrees or isolated directories for parallel coding.** Never let multiple agents mutate the same repo/workdir simultaneously.
6. **Escalate only on evidence.** Failed simple tier -> medium tier -> maximum/planning tier.
7. **Record reusable outputs under artifacts workspace:**

```text
/mnt/c/Users/santi/Documents/Hermes/Artifacts/YYYY-MM-DD/HH-MM-SS/<PascalCasePurpose>/
```

Use PascalCase for files/folders under `Documents/Hermes`, except date/time folders and file extensions. Do not write new plans to Desktop.

8. **Load `task-artifacts-delivery` when orchestration produces durable plans, reports, summaries, or media.** That skill carries Xan's artifact layout, plan-preview, Telegram MP3, and voice-summary preferences.

9. **For multi-machine Hermes setups, use federated skill sharing instead of global blind sync.** Controller-owned `core-common`, `init`, and `comms` skills can be imported by child agents; `local-adapted` and `private` skills stay local unless reviewed and promoted. Agent self-updates and cross-agent proposals use the Shared Drawer protocol at `C:\Users\santi\Documents\Hermes\Shared Drawer\Protocols\agent-self-update-protocol.md`. See `references/federated-agent-skill-sharing.md`.

## Configuration Storage

Use native Hermes config only for runtime settings Hermes actually reads: models, providers, STT/TTS, gateway, toolsets, memory, security.

Use the shared workspace config for user-facing orchestration policy:

```text
C:\Users\santi\Documents\Hermes\Config\ModelRouting.yaml
```

Use memory only for compact routing preferences that should influence future sessions immediately. Use skills for reusable orchestration procedures. Do not store secrets in `Hermes/Config`.

## Main-Only Init Authority

For Hermes child-agent/laptop bootstrap work, the main/controller machine owns reusable init/bootstrap authority. Child machines may run a one-time extracted init package, but they should not receive reusable init skills by default.

Default child-safe imports are `plan-mode`, `get-artifact`, `storage-explorer`, `file-organization`, `omni-qa`, `image-gen`, `meta-gateway`, `get-movie`, `get-show`, `get-music`, generic `SOUL.md`, Xan preference seed memory, sync policy, and agent message contract. Do not copy private keys, raw `.env` files, raw memory dumps, or another machine's `local-adapted`/`private` skills into child seeds.

Preferred one-time init bundle layout:

```text
init/
  init                   # optional empty trigger marker; read init_prompt.md first, not authority by itself
  README.md
  init.py
  init_prompt.md          # first-class package-run prompt
  src/
  skills/
  memories/
  seeds/
  docs/
```

See `references/main-only-init-authority.md` for the full package policy, empty `init` trigger-marker handling, and `init_prompt.md` first-class expectations.

## Worker Selection

### Direct Hermes tools

Use for:

- reading/writing specific files
- running tests
- small shell commands
- deterministic transformations
- browser automation
- system diagnostics

Why: fewer moving parts. External agents are not magic; they are expensive ambiguity generators if overused.

### Gemini CLI

Use for:

- simple and medium reasoning lanes
- quick summaries and low-risk code review
- generating candidate patches or checklists
- comparing options cheaply

Default routing:

- `Gemini 3.5 Flash` for simple tasks
- `Gemini 3.1 Pro` for medium tasks

Probe first because Gemini CLI syntax/model names may differ:

```bash
command -v gemini
timeout 10s gemini --help
```

Safe one-shot pattern, adjusted to actual CLI syntax after probing:

```bash
gemini -m <model-alias> -p "<bounded prompt>"
```

If the CLI hangs or enters an interactive session, run it with `pty=true` or avoid it until auth/config is fixed.

### Antigravity

Observed on Xan's host:

```text
/mnt/c/Users/santi/AppData/Local/Programs/Antigravity/bin/antigravity
C:\Users\santi\AppData\Local\Programs\Antigravity\bin\antigravity.cmd
```

Antigravity currently behaves like a VS Code-family desktop launcher. It supports opening folders/files, extension management, MCP registration, and diagnostics. A verified headless Composer-style task CLI was not observed.

Use Antigravity for:

- opening a repo/workspace for human-supervised agent work
- installing/configuring MCP servers into Antigravity
- using its UI/agent affordances when visible desktop interaction is acceptable

Reliable launch from WSL:

```bash
powershell.exe -NoProfile -Command "& 'C:\\Users\\santi\\AppData\\Local\\Programs\\Antigravity\\bin\\antigravity.cmd' 'C:\\path\\to\\repo'"
```

Avoid invoking the WSL shell wrapper directly when it fails with UNC/EPERM paths. Use PowerShell from a Windows working directory.

Antigravity MCP add pattern:

```bash
powershell.exe -NoProfile -Command "& 'C:\\Users\\santi\\AppData\\Local\\Programs\\Antigravity\\bin\\antigravity.cmd' --add-mcp '{\"name\":\"server-name\",\"command\":\"cmd-or-exe\",\"args\":[\"arg1\"]}'"
```

### Cursor / Composer

Observed path may be Windows-installed:

```text
/mnt/c/Program Files/cursor/resources/app/bin/cursor
```

Use Cursor for:

- opening workspaces for Composer/manual UI use
- Cursor-specific workflows when its CLI exposes an agent/composer subcommand

Probe before assuming Composer CLI exists:

```bash
command -v cursor
cursor --help
cursor --version
```

If Composer has no verified headless CLI, do not pretend it does. Launch the workspace and use browser/computer-use only if the environment supports UI interaction.

### Codex fallback

Use when Gemini/Antigravity/Cursor are unavailable or inappropriate and Codex CLI is installed/authenticated.

Probe:

```bash
command -v codex
codex --version
codex --help
```

Use existing `codex` skill patterns:

```bash
codex exec "<bounded prompt>"
```

Codex generally needs a git repo and often benefits from `pty=true`.

### OpenCode fallback / alternative

Use when installed/authenticated and provider routing is already configured.

Probe:

```bash
command -v opencode
opencode --version
opencode auth list
```

One-shot:

```bash
opencode run "<bounded prompt>" --model <provider/model>
```

### Agent self-documentation / fork constructor bundles

Use this pattern when Xan asks to reproduce, fork, clone, document, or bootstrap an agent from lived context rather than just code. The goal is a constructor packet: enough layered context for the new agent to inherit behavior, not merely configuration.

Minimum bundle sections:

- identity + role map;
- skill/plugin inventory;
- gateway/plugin architecture;
- memory/artifact system;
- init/bootstrap sequence;
- communication protocols;
- implicit behaviors/learned patterns;
- known gaps/upgrade notes;
- reproduction checklist;
- raw self-model.

Supporting artifacts should include sanitized config, env key names only, source/workspace tree snapshots, skill/plugin inventories, DB schemas/counts, relevant protocol/comms snapshots, copied core skill files, manifest, QA report, and hash file. Never include raw `.env` values, private keys, auth stores, browser profiles/cookies, raw transcript dumps, or full logs. Run `omni-qa` before delivery and state what was not verified: the fork is not proven alive until it boots and performs its own first-response QA.

See `references/2026-05-26-agent-self-documentation-reproduction-bundles.md`.

### Federated Hermes child agents

Use when creating durable child agents on other machines over SSH/Tailscale.

Design principle: agents should share common/init/comms knowledge, not blindly synchronize all skills and memory. Each machine agent grows `local-adapted` skills for its own environment, while the controller reviews and promotes only genuinely reusable knowledge.

Portable child-agent seed files should include:

- generic `SOUL.md` with operating traits but no Wilson-specific character reference
- Xan preference seed for response style, workflow, artifact delivery, and verification defaults
- `plan-mode` skill
- sync policy distinguishing `core-common`, `init`, `comms`, `local-adapted`, and `private`
- child-to-controller message contract

- `references/federated-agent-skill-sharing.md` — federated skill/memory sharing model, promotion flow, and class boundaries.
- `references/shared-drawer-agent-self-update.md` — Lazarus/LilJon Shared Drawer protocol for memory, SOUL, skill, and bundle candidates.

## Computer Use From WSL

Hermes in WSL can reliably use:

- terminal tools inside WSL
- Windows executables through `/mnt/c/...` or `powershell.exe`
- file access to Windows drives under `/mnt/c`, `/mnt/d`, etc.
- browser automation through the configured browser toolset

Full desktop GUI computer-use from WSL is conditional. If the active `computer_use` tool is marked macOS-only or no Windows desktop bridge is configured, assume **no reliable full Windows desktop control**. Launching Antigravity/Cursor is possible; controlling their UI is only reliable if a browser/computer-use/VNC/desktop automation bridge is present and tested.

Do not claim GUI control until verified with a harmless smoke test: open app, observe window, click/type, close or leave unchanged.

## Orchestration Procedure

1. **Classify the task.**
   - simple / medium / maximum / planning
   - code / research / ops / UI / document
   - read-only vs mutating
2. **Show plan summary** unless explicitly skipped.
3. **Probe worker readiness if not already known.**
4. **Select worker and model tier.**
5. **Create isolation if mutating code.**
   - git branch, worktree, temp clone, or artifact folder
6. **Run worker with bounded prompt.** Include:
   - allowed paths
   - forbidden paths
   - output format
   - tests/verification required
   - stop conditions
7. **Monitor.** Use `process` for background workers.
8. **Verify independently.** Read diffs, run tests, inspect logs.
9. **Escalate if needed.** Do not loop blindly.
10. **Summarize results.** Include worker used, model tier, files changed, tests run, risks.

## Prompt Template for Workers

```text
You are a bounded worker agent. Task: <task>.

Allowed paths:
- <path>

Forbidden paths:
- ~/Desktop unless explicitly permitted
- secrets, keys, vaults, backups unless explicitly permitted

Model tier: <simple|medium|maximum|planning>
Expected output:
- concise findings or patch summary
- files changed
- commands/tests run
- remaining risks

Rules:
- Do not modify outside allowed paths.
- Do not expose secrets.
- Stop and report if blocked.
```

## Reference Material

- `references/main-only-init-authority.md` — main-controller-only bootstrap authority, child-safe seeds, child-agent registry array, and Windows OpenSSH administrator authorized-keys trap.
- `references/child-agent-handoff-bundles.md` — self-contained ZIP handoff pattern for sending init/repair bundles to another agent, including README shape, registry snapshot, and Telegram visible summary requirements.
- `references/2026-05-26-agent-self-documentation-reproduction-bundles.md` — constructor-facing self-documentation/fork bundle pattern: required sections, raw inventories, redaction boundary, core skill sub-artifacts, and QA expectations.

## Verification Checklist

- [ ] Plan summary shown unless skipped
- [ ] Worker readiness probed or already known
- [ ] Model tier chosen deliberately
- [ ] Mutating work isolated
- [ ] Desktop not touched unless approved
- [ ] Secrets avoided/redacted
- [ ] Diffs/logs/tests verified by Hermes
- [ ] Artifact saved under Documents/Hermes/Artifacts when durable
- [ ] Final answer states observed facts vs inference

## Common Pitfalls

1. **Assuming Antigravity has a headless agent CLI.** Current verified CLI is VS Code-family launcher/MCP/extension tooling. Use UI workflows only when UI control is verified.
2. **Assuming Cursor Composer has a stable CLI.** Probe first. Cursor's launcher is not necessarily Composer automation.
3. **Letting workers share a dirty workdir.** Use worktrees or separate directories.
4. **Skipping independent verification.** Worker self-reports are not evidence.
5. **Hardcoding model names forever.** Model aliases drift. Treat the tier table as configurable defaults.
6. **Using maximum models for cheap tasks.** Wasteful and slower.
7. **Forgetting WSL/Windows path translation.** Prefer Windows paths for Windows apps, WSL paths for Hermes file tools.
