---
name: omni-qa
description: Use when performing QA across Hermes code, skills, plugins, gateway behavior, init packages, multi-agent protocols, artifacts, or any agent-produced system change; defines a universal evidence-first quality gate.
version: 1.0.0
author: Wilson / Hermes Agent
license: MIT
platforms: [windows, wsl, linux]
metadata:
  hermes:
    tags: [qa, verification, hermes-agent, skills, plugins, gateway, code, artifacts, init, multi-agent]
    related_skills: [hermes-agent, hermes-extension-quality-assurance, hermes-agent-skill-authoring, meta-gateway, file-organization]
---

# Omni QA

## Overview

Use this skill as the general QA pass for anything I touch: code, skills, plugins, gateway behavior, init/update bundles, multi-agent protocols, artifacts, scripts, configs, and file operations.

The rule is simple: no ungrounded green lights. QA means observed checks, explicit scope, blockers separated from warnings, and a clear statement of what was not verified. Anything else is decorative smoke.

## When to Use

Use when Xan says or implies:

- `QA this`, `review this`, `sanity check`, `quality pass`, `test it`, `verify it`.
- `QA for everything you` / global quality assurance across my own output.
- Changes touch Hermes Agent code, skills, plugins, tools, gateway, cron, profiles, MCP, init packages, or multi-agent coordination.
- A generated artifact, script, manifest, cleanup plan, or protocol will be reused later.
- Another agent produced a result and Wilson must verify it before telling Xan it worked.

Do not use as a replacement for domain-specific skills. Load the relevant domain skill first, then use this as the QA layer.

## QA Operating Model

Always report QA using these buckets:

```text
Scope: what was checked
Evidence: commands/files/tools used
Pass: verified facts
Warnings: non-blocking risks or convention drift
Blockers: must fix before use
Not verified: explicit limits
Next action: safest follow-up
```

If no tests/checks were run, say so. Do not imply verification from intention.

## Universal QA Checklist

1. **Intent match**
   - Does the result actually satisfy Xan's request?
   - Are names, paths, and scope aligned with the latest correction?
   - Are stale assumptions removed?

2. **Structural validity**
   - Files exist where claimed.
   - Frontmatter / JSON / YAML / TOML / scripts parse.
   - Zips contain expected entries.
   - Manifests and signatures are internally consistent.

3. **Behavioral verification**
   - Run the narrowest meaningful test or command.
   - Prefer deterministic checks over eyeballing.
   - For code: run targeted tests, syntax checks, lint where available.
   - For gateway/protocol changes: verify transport, message envelope, delivery, and result path.

4. **Safety review**
   - Identify destructive actions, credential exposure, private keys, raw env files, browser profiles, firewall/public exposure, persistence/autostart, and broad file moves/deletes.
   - Confirm those are either absent or explicitly approved.

5. **Regression risk**
   - Check whether the change impacts prompt caching, role alternation, session routing, tool availability, platform behavior, or cross-agent authority.
   - If a broad regression suite is too expensive, say what narrow suite was used and why.

6. **Artifact integrity**
   - For generated files: verify size, hash when transferred, and readability.
   - For archives: list contents and verify required files exist.
   - For transferred artifacts: compare source/destination hashes.

7. **Documentation and state**
   - Update `STATE.md` for tool-heavy runs, config edits, skills/plugins changes, memory writes, or multi-step investigations.
   - Patch relevant skills immediately if the QA pass exposes a missing pitfall.

## Hermes Code QA

For Hermes Agent code changes:

- Load `hermes-agent` and any relevant software-development skill.
- Inspect git diff before finalizing.
- Run syntax/compile checks for touched Python files.
- Run targeted pytest with `-o 'addopts='` where practical.
- If tests cannot run, record exact reason.
- Watch for:
  - prompt cache invalidation
  - message role alternation
  - config/profile safety
  - `get_hermes_home()` usage
  - gateway session routing
  - tool schema stability
  - Windows/WSL path behavior

## Skill QA

For `SKILL.md` and skill bundles:

- Frontmatter starts at byte zero with `---`.
- YAML parses.
- Required fields: `name`, `description`.
- Description <= 1024 characters.
- Body is non-empty.
- Skill name matches directory/bundle intent.
- Trigger conditions are clear.
- Common pitfalls and verification steps exist for non-trivial workflows.
- Related skills are relevant and not fantasy references.
- If bundled for child agents, confirm it is child-safe and contains no secrets or local-only private data.

## Plugin QA

For Hermes plugins:

- `plugin.yaml` parses and has expected metadata.
- Entrypoint exports/registers the expected `register(ctx)` behavior or a known alternate registrar.
- Tool schemas are stable and handlers return JSON strings.
- Plugin-scoped skills are discoverable by qualified name where applicable.
- Self-test path exists for QA plugins.
- Registration tests run when the plugin loader changed.

## Gateway / Messaging QA

For Telegram, gateway, or cross-platform changes:

- Verify target routing, chat/thread selection, and delivery semantics.
- Avoid platform-specific formatting that breaks the target.
- For Telegram: no markdown tables; use bullets/labeled fields.
- Attach artifacts with `MEDIA:` when Xan needs the file in-chat.
- For TTS: generate only the short spoken summary, not the full response.
- Check logs or direct delivery status when available.

## Init / Multi-Agent QA

For `init.zip`, child-agent updates, or meta-gateway changes:

- Archive is named `init.zip`.
- Fresh agent instruction is present: read `init_prompt.md` and follow it.
- Stable approve-once commands remain unchanged unless intentionally versioned.
- Controller update manifest and signature verify.
- Bundle contains expected child-safe skills and no private keys/secrets.
- SSH/SCP/Tailscale delivery is verified with hashes when sent.
- Subordinate execution must report back through Wilson for Telegram visibility.
- Destructive/security-sensitive operations remain approval-gated.

## File / Artifact QA

For file organization, cleanup, or storage work:

- Inspection and deletion are separate phases.
- Dry-run manifests precede moves/deletes unless Xan gave exact approved targets.
- Duplicates require hash verification before deletion.
- Protected personal/family media and backups are not treated as junk.
- Move plans include restore path/script for actual execution.
- Post-action verification checks source/destination state.

## Final QA Report Template

```text
## QA Pass

Scope:
- ...

Evidence:
- ...

Pass:
- ...

Warnings:
- ...

Blockers:
- None / ...

Not verified:
- ...

Next action:
- ...
```

## Reference Material

- `references/2026-05-26-arby-consolidated-architecture-qa.md` — signed child-agent init/update QA pattern: canonical skill rename, old-name scans, manifest default validation, signature verification, transfer hashing, and separating delivery from subordinate execution.
- `references/2026-05-26-emma-self-documentation-bundle-qa.md` — constructor-facing self-documentation bundle QA pattern: redaction boundary, raw inventories, core skill sub-artifacts, secret-scan false positives, manifest/QA/hash files, and fork reproduction caveats.

## Common Pitfalls

1. **Testing the wrong thing.** A syntax pass is not a behavioral pass. Label it correctly.
2. **Treating warnings as blockers.** Keep the severity boundary clean.
3. **Silent transfer trust.** If a file crosses machines, hash both ends when feasible.
4. **Skill-name drift.** If Xan renames a workflow, update prompts, bundles, manifests, shared protocols, coordination messages, and related skills. Then scan generated archives for the old name before delivery. Old names breed zombie instructions.
5. **Secret-scan false positives.** Naive token regexes can flag ordinary skill names like `task-artifacts-delivery` because they contain `sk-` inside a word. Refine with token boundaries/provider-like prefixes and manually review hits before blocking delivery.
6. **Overbroad QA claims.** If only the package compiled, don't claim the architecture is proven.
7. **Forgetting `STATE.md`.** QA runs are audit events when they patch skills, configs, protocols, or artifacts.

## Verification Checklist

- [ ] Relevant domain skill loaded first.
- [ ] Scope and evidence are explicit.
- [ ] Required static validations passed or blockers listed.
- [ ] Runtime/behavior tests run where practical.
- [ ] Safety-sensitive categories reviewed.
- [ ] Artifacts/transfers verified when present.
- [ ] `STATE.md` updated for durable changes.
- [ ] Final report separates pass/warnings/blockers/not-verified.
