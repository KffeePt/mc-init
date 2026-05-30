# Agent Comms Mailbox QA + Notification Layer Notes

Session pattern: Xan asked whether Wilson and Arby had real SCP/file transfer and a token-efficient agent-to-agent coordination protocol, then asked for a QA pass and notification behavior.

## Verified shape

- Wilson/Lazarus can reach Arby/LilJon over Tailscale SSH.
- Wilson -> Arby SCP works.
- Wilson -> Arby mailbox delivery works: JSON message files land in Arby's inbox.
- Arby -> Wilson is intentionally pull-based because Wilson inbound SSH remains closed.
- Arby can place JSON files in its outbox; Wilson pulls them and archives remote outbox files into Arby's sent folder.
- Wilson-side listener can poll, pull, log, and archive messages without LLM tokens.

## Important QA distinction

Transport working is not the same thing as notification consumption working.

In QA, Arby's inbox contained Wilson messages. That proved delivery, but also proved Arby-side consumption/forwarding was not active yet. Report this as:

- **Transport:** working.
- **Wilson listener:** running if process exists.
- **Arby notifier/consumer:** only working if Arby's inbox drains and a log/notification output is produced.

Do not claim "Arby will notify Xan" merely because messages can be delivered to Arby's inbox.

## Safe protocol rule

Mailbox payloads must not be auto-executed by default. The safe listener pattern is:

1. Pull or read message JSON.
2. Validate schema: id/from/to/type/timestamp/payload.
3. Log notification metadata.
4. Archive to processed/sent.
5. Only execute commands through a reviewed, explicit handler with allowlisted actions.

This avoids turning a coordination layer into unattended remote code execution.

## Message contract for token-efficient notifications

Senders should encode task context programmatically so a receiver does not need an LLM to interpret it:

```json
{
  "id": "wilson-...",
  "from": "wilson",
  "to": "arby",
  "type": "agent_notification",
  "timestamp": "2026-05-25T00:00:00Z",
  "payload": {
    "agent": "wilson",
    "body": "lazarus",
    "action": "deploy|download|scan|cleanup|transfer|alert|coordination",
    "status": "started|progress|completed|failed|blocked",
    "subject": "short human label",
    "intent": "why this is happening",
    "details": "optional short context",
    "artifacts": ["optional paths"],
    "requires_user": false
  }
}
```

For Telegram notifications, format from those fields directly. Do not call an LLM just to summarize a structured notification.

## QA checklist

- [ ] `bash -n` passes for Wilson script, Arby script, and listener.
- [ ] Wilson -> Arby `ping` returns PONG.
- [ ] Wilson inbox/outbox counts are sane; no stuck outbox except quarantined failed test messages.
- [ ] Arby script exists at `C:\Users\santi\Documents\Hermes\Scripts\agent-comms.sh`.
- [ ] Arby inbox receives a test message.
- [ ] Arby outbox pull moves remote messages to Arby's sent folder.
- [ ] Listener does not auto-execute payloads.
- [ ] If user asks for notifications, verify the consuming side drains inbox and writes/sends notifications.

## Pitfalls

- Windows SSH may run `cmd` semantics; `mkdir -p` is wrong against Windows SSH unless explicitly going through WSL. Use `cmd /c mkdir` for Windows mailbox paths.
- Missing execute bits can make a listener fail if it tries to invoke a script directly. Use `bash /path/to/script.sh` inside shell listeners.
- A stale failed outbox file from a pre-fix test should be moved to `failed/`, not retried forever.
- Do not open Wilson inbound SSH just for symmetry. Pull-based messaging is safer for the controller.