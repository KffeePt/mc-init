# 2026-05-26 Emma self-documentation bundle QA

## Context

Xan requested a full recursive self-documentation artifact bundle to reproduce Wilson as a fork named `emma`. The run produced markdown section artifacts, raw inventories, core skill sub-artifacts, sanitized config context, source/workspace tree snapshots, comms/protocol snapshots, a ZIP, and a QA report.

## Durable QA pattern

Use this pattern for constructor-facing self-documentation, init/update bundles, and agent reproduction packages:

1. Load the domain skills first: `hermes-agent` for Hermes internals, `task-artifacts-delivery` for bundle hygiene, `meta-gateway`/`orchestration` for multi-agent authority, and this `omni-qa` skill for the quality gate.
2. Create a timestamped artifact folder under the shared Hermes workspace.
3. Collect live inventories, but sanitize aggressively:
   - sanitized config only;
   - `.env` key names only;
   - skill inventory and selected copied SKILL.md files;
   - plugin metadata/file inventory;
   - DB schemas/counts, not transcript dumps;
   - log file inventory, not raw log contents;
   - bounded source/workspace trees;
   - comms/protocol snapshots where useful.
4. Write explicit section artifacts instead of one huge monolith when the user asks for reproducible constructor context.
5. Include a manifest, QA report, and hash file.
6. Package as ZIP and attach via `MEDIA:`.
7. Update `STATE.md` for auditability.

## Secret scan pitfall

Naive secret regexes such as `sk-[A-Za-z0-9_-]{12,}` can false-positive on ordinary skill names like `task-artifacts-delivery` because they contain `sk-` inside a word. Refine secret scans so `sk-` tokens require a token boundary and/or provider-like prefixes (`sk-live`, `sk-proj`, etc.), then manually inspect any remaining hits.

Example safer OpenAI-like rough pattern:

```regex
(?<![A-Za-z])(sk-(?:live|test|proj|ant|or|)[A-Za-z0-9_\-]{16,})
```

Do not claim "no secrets" from a single regex. Claim only what was checked: e.g. "refined secret-pattern scan produced no hits; raw `.env` values, private keys, browser profiles, and transcript dumps were intentionally excluded."

## QA report shape used

```text
Scope:
- requested sections
- raw inventories
- core skill sub-artifacts
- bundle packaging
- secret-pattern scan
- STATE update

Evidence:
- files written
- ZIP exists/nonzero
- required markdown present
- raw inventories present
- core skill files copied
- refined secret scan result

Pass:
- bundle exists
- sections represented
- config sanitized
- env values excluded
- ZIP attached

Warnings:
- plugin runtime enablement inferred from files/config
- source/gateway behavior documented from inspection, not exhaustive formal trace
- hidden/injected instructions must be explicitly encoded for the fork

Blockers:
- none, or list potential secret hits until reviewed

Not verified:
- actual fork construction
- fork first-live-response QA
```

## Constructor-facing redaction boundary

Include enough context to reproduce behavior, not enough to leak the user:

- Include: skill files, sanitized config, env key names, source tree, protocols, schemas/counts, operating guides, reproduction checklist.
- Exclude: raw env values, private keys, auth stores, browser profiles/cookies, raw transcript dumps, full logs, credential vaults.

## Value of this pattern

The artifact bundle becomes a reproducible constructor packet rather than a vague summary. The QA boundary is explicit, and future agents know exactly what was observed, copied, sanitized, excluded, and not verified.