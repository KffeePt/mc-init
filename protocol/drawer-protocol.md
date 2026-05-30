# Drawer Protocol

The `drawer` repo is the shared remote state/comms drawer for controller and subordinate Hermes/OpenClaw-style agents.

## Authority

- `main` is controller-only.
- Subordinates use `drawer/<group>/<agent-name>-<computer-label>`.
- `mc-init` remains the source of truth for schema and bootstrap policy.
- `drawer/schema/` may contain a published copy for offline/subordinate access.

## Sync

Scheduled sync uses: lock -> fetch -> checkpoint -> rebase -> push -> push checkpoint tag -> unlock.

Scheduled sync must never hard reset or force push.

## Conflict Stall

On conflict or remote failure, the agent writes `.drawer/conflict.json`, pauses scheduled sync, emits a notification envelope, and waits for controller/human resolution.

## Transports

Direct SSH/SCP/Tailscale/Hermes gateway is preferred. Git drawer is fallback async transport for off-network coordination.
