# 2026-05-22 — Artifact Workspace, Planning, and Voice Delivery Preferences

## Trigger

Xan corrected the assistant's operating workflow and delivery format during a Hermes/Telegram session.

## Durable lessons

### Response clarity

The assistant had been too terse — “caveman” mode was hard to understand. Xan wants concise, high-signal output, but not cryptic output. The right balance is:

- succinct
- technically precise
- enough context to understand the decision/action
- no filler
- no fake politeness

### Artifact organization

Plans, walkthroughs, summaries, reports, and other durable user-AI artifacts should live under:

```text
C:\Users\santi\Documents\Hermes\.artifacts\YYYY-MM-DD\HH-MM-SS\<type-or-purpose>\
```

WSL equivalent:

```text
/mnt/c/Users/santi/Documents/Hermes/.artifacts/YYYY-MM-DD/HH-MM-SS/<type-or-purpose>/
```

Do not create new plans/artifacts on Desktop. If an artifact was previously put on Desktop, do not move or delete it unless Xan approves.

### Planning flow

Before multi-step or file/system-changing work, show a short plan summary unless Xan explicitly says `skip plan` or equivalent.

The plan should cover:

- scope
- intended changes
- affected paths
- risks
- approval needed

### Voice summaries

At the end of completed tasks, Xan wants a short paragraph-length voice summary when feasible, alongside the normal text summary.

Telegram-compatible preference:

- use `.mp3`
- avoid `.wav` unless requested

Cheap/reliable voice defaults:

```yaml
tts:
  provider: edge

stt:
  enabled: true
  provider: local
  local:
    model: base
```

Rationale:

- Edge TTS is free and produces MP3 reliably.
- Local faster-whisper avoids API cost and quota dependency.

## Example final media delivery

```text
MEDIA:/mnt/c/Users/santi/Documents/Hermes/.artifacts/YYYY-MM-DD/HH-MM-SS/summaries/task-summary.mp3
```
