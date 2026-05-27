# Agent-to-Agent Protocol

Canonical source: `Hermes/Init/protocol/`
Mirrored in: init.zip bundles for child agents

## Hierarchy

```
Xan (human owner)
  └── Wilson / Lazarus (main controller)
        └── Arby / LilJon (subordinate child machine)
        └── <future agents> (subordinate workers unless promoted)
```

## Request Envelope

All cross-agent operations must use this envelope:

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

## Allowed Operations (No Fresh Approval)

- SSH connectivity tests
- Local status checks
- Registry/situational-awareness collection
- Non-destructive artifact creation
- Installing child-safe seed files during approved init
- Implanting controller public SSH key during approved init

## Requiring Explicit Xan Approval

- Destructive commands
- Credential export
- Private-key transfer
- Raw `.env` transfer
- Browser profile/cookie transfer
- Public firewall exposure
- Persistence/autostart changes
- Broad recursive deletion/move operations
- Subordinate overwriting controller registries

## Communication Channels

| Channel | Direction | Protocol | Auth |
|---|---|---|---|
| SSH | Wilson → Arby | OpenSSH + Tailscale | Ed25519 key |
| SCP/SFTP | Wilson ↔ Arby | SSH + Tailscale | Ed25519 key |
| Agent Comms Mailbox | Wilson ↔ Arby | JSON + SCP | SSH |
| Taildrop | Wilson → Arby | Tailscale | Tailnet |
| Shared Drawer | Wilson ↔ Arby | Windows SMB/SCP | File ACL |
| Telegram | Arby → Xan | Hermes Gateway | Bot token |

## Init Bootstrap Flow

1. Wilson builds `init.zip` via `scripts/build-init.sh`
2. Wilson publishes via `scripts/publish-init.sh <agent>`
3. Child agent extracts and reads `init_prompt.md`
4. Child agent runs `py .\init.py approved-init --replace-authorized-keys`
5. Child agent verifies SSH, Tailscale, skills
6. Child agent creates and returns `init_res.zip`
7. Wilson ingests situational awareness data
8. Wilson relays status to Xan via Telegram
