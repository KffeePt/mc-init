# 2026-05-26 Arby consolidated architecture QA

## Context

Xan corrected the child-agent default skill architecture:

- Canonical file organization skill name is `file-organization` only.
- Old personal-prefixed file organization naming should not remain in default/global child-agent packages.
- `omni-qa` is the universal QA layer: QA for code, skills, plugins, gateway, init packages, artifacts, protocols, and agent-produced system changes.
- Custom Arby/LilJon updates must consolidate architecture, not just copy changed files.

## Durable pattern

When a skill is renamed or promoted into the default/global child-agent set, QA must cover more than the local skill directory:

1. Create or patch the canonical skill.
2. Remove or absorb the superseded skill if it would otherwise remain as an active duplicate.
3. Patch active skill references and shared protocols.
4. Rebuild child-agent init/update bundles from the canonical skill set.
5. Scan the bundle paths and text files for the old name.
6. Verify `controller_update.json` default skills exactly match the intended list.
7. Verify signed controller update manifests with `ssh-keygen -Y verify` when the package uses signed updates.
8. Compile/syntax-check packaged code touched by the update.
9. If the package is sent to another machine, compare source and destination hashes after transfer.
10. If a mistake is found after transfer, rebuild, resend, and re-hash the corrected artifact; do not leave the stale copy as the implied final one.

## Consolidated default child-safe/global skills

Current intended list from this session:

```text
plan-mode
get-artifact
storage-explorer
file-organization
omni-qa
image-gen
meta-gateway
```

## QA report shape

Use the `omni-qa` report sections:

```text
Scope
Evidence
Pass
Warnings
Blockers
Not verified
Next action
```

For child-agent updates, `Not verified` usually includes subordinate-side execution until the target machine applies the update and returns its own report.

## Pitfalls

- Renaming only the local skill leaves zombie references in protocols, init prompts, bundled skills, manifests, or coordination messages.
- A valid signature only proves the manifest content; it does not prove the zip contains every expected skill or lacks old strings.
- A successful SCP transfer is not enough. Hash the remote copy.
- Do not claim Arby/LilJon applied an update just because the archive was delivered. Delivery and execution are separate facts.
