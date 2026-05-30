# Wilson ↔ Arby Agent Comms Mailbox Layer — 2026-05-25

Session pattern for token-efficient lateral coordination between Xan's controller agent and subordinate laptop agent.

## What was built

A lightweight JSON mailbox protocol over the already-secure Tailscale + Windows OpenSSH path.

- Wilson/Lazarus pushes JSON messages directly into Arby's inbox with SCP.
- Arby/LilJon can leave JSON messages in its outbox.
- Wilson pulls Arby's outbox because Lazarus inbound SSH remains closed.
- A Wilson-side listener polls/pulls/logs/archives messages but does **not** auto-execute payloads.

## Paths

Wilson/Lazarus:

```text
/home/xantastique/.hermes/scripts/agent-comms.sh
/home/xantastique/.hermes/scripts/agent-comms-arby.sh
/home/xantastique/.hermes/scripts/agent-comms-listener.sh
/mnt/c/Users/santi/Documents/Hermes/Comms/wilson/
```

Arby/LilJon:

```text
C:\Users\santi\Documents\Hermes\Scripts\agent-comms.sh
C:\Users\santi\Documents\Hermes\Comms\arby\
```

## Verified behavior

- Wilson → Arby SSH ping works.
- Wilson → Arby SCP works.
- Wilson → Arby mailbox delivery works.
- Arby → Wilson mailbox transfer works by Wilson pulling Arby's outbox.
- Arby direct SSH into Wilson is not available because Lazarus inbound SSH is closed; keep it that way unless Xan explicitly approves opening central SSH.

## QA pitfalls found

1. Remote mailbox creation must use Windows-compatible `cmd /c mkdir ...`, not Linux `mkdir -p`, because Windows OpenSSH command execution does not necessarily run inside WSL.
2. Message IDs should not depend on optional binaries like `xxd`; use `od`/stdlib-compatible randomness instead.
3. Pulling from a remote outbox must archive/move the remote messages after local ingestion, otherwise every pull can duplicate them.
4. A mailbox listener must not auto-execute arbitrary `command` payloads. It should log/archive and require a reviewed handler for execution semantics.
5. Delivery and consumption are different checks: Arby inbox containing Wilson messages proves transport, but also proves Arby-side notification consumption is not active yet.

## Message schema

Use small JSON files:

```json
{
  "id": "wilson-epoch-pid-random",
  "from": "wilson",
  "from_body": "lazarus",
  "to": "arby",
  "type": "coordination",
  "timestamp": "UTC_ISO8601",
  "payload": "short structured string or JSON-encoded object"
}
```

Recommended types:

```text
notification
coordination
query
response
file_transfer
command
```

For notifications, encode intent/status in the payload so the receiving side can forward or display without spending LLM tokens:

```json
{
  "action": "download|deploy|config|scan|transfer|alert",
  "subject": "short what",
  "intent": "short why",
  "status": "started|progress|completed|failed|blocked",
  "details": "optional concise context",
  "agent": "wilson",
  "body": "lazarus"
}
```

## Security decision

Use pull-based Arby → Wilson communication by default. Opening SSH inbound on Lazarus expands the central attack surface and should be a deliberate user-approved change, not a convenience toggle.
