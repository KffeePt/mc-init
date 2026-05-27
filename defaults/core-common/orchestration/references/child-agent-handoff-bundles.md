# Child-agent handoff bundles

Session signal: after Arby/laptop bootstrap work, Xan asked to "send me the bundle to send the other agent." The useful pattern is a self-contained handoff ZIP plus visible Telegram summary.

## Bundle contents

For child-agent initialization or repair, package a ZIP with:

- `init.zip` — patched one-time bootstrap package.
- A focused repair script when relevant, e.g. Windows SSH admin-authorized-keys fix.
- `children.json` — controller-side child-agent registry snapshot. This is an operational roster, not an auth database.
- `README-<agent>-HANDOFF.md` — explicit instructions for the receiving agent.

Never include private keys, tokens, `.env` files, raw memory dumps, cookies, or reusable init authority skills in the child handoff.

## README structure

Use this shape:

```md
# <Agent> Child Agent Bootstrap Bundle

## Contents
## Recommended path for the other agent
## Important constraints
## Verification to report back
```

The other agent should report back using the agent message contract:

```text
## Result
## Observed Facts
## Actions Taken
## Files / Artifacts
## Verification
## Risks / Assumptions
## Proposed Skill Promotions
## Remaining Work
```

## Telegram delivery

When delivering to Xan, include:

1. A PNG visual summary.
2. The ZIP bundle.
3. A short matching TTS/audio summary.

The PNG/audio summary should say what the bundle contains, what the receiving agent should do, and remaining verification. Do not force Xan to open a ZIP to know whether it is the right thing.

## Windows SSH repair note

If Windows OpenSSH is reachable but key auth fails for an administrator account, include a repair script that writes the controller public key to:

```text
C:\ProgramData\ssh\administrators_authorized_keys
```

with ACLs for `Administrators:F` and `SYSTEM:F`, and restarts `sshd`. Also update the child-agent registry record status so the controller can distinguish "reachable but auth failed" from "not reachable".
