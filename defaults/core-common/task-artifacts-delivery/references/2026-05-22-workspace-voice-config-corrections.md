# 2026-05-22 Workspace, Voice, and Config Corrections

Session-specific details captured from Xan's corrections.

## User-facing delivery corrections

- Do not over-compress responses into hard-to-read "caveman" phrasing.
- Prefer compact bullets, short labels, and `->` for source/destination or flow relationships.
- For straightforward human-response requests, direct MP3 voice is acceptable when feasible, but include compact text summary so the answer still works when audio cannot be heard.
- For voice summaries, do not speak literal filenames, paths, commands, URLs, IDs, or model strings by default. Use short labels instead.

## Workspace corrections

- Canonical shared workspace:

```text
C:\Users\santi\Documents\Hermes\
```

- Canonical artifact root:

```text
C:\Users\santi\Documents\Hermes\Artifacts\YYYY-MM-DD\HH-MM-SS\<PascalCasePurpose>\
```

- Use PascalCase for files/folders under `Documents/Hermes`, except date folders, time folders, and normal lowercase file extensions.
- Do not create new artifacts on Desktop.
- Do not touch Desktop unless explicitly approved.

## Scripts convention

Future reusable scripts and one-time scripts worth keeping belong under:

```text
C:\Users\santi\Documents\Hermes\Scripts\<ScriptPurpose>.<ext>
```

Each saved script should include a short header:

- Purpose
- Date
- Inputs
- Outputs or side effects
- Safety notes

## Config storage recommendation

Use the right layer:

- `~/.hermes/config.yaml` -> native Hermes runtime settings only: model, providers, tools, STT/TTS, gateway, memory, security.
- `Hermes/Config/*.yaml` -> shared user-facing operating policies: workspace layout, routing preferences, sanity/discovery policies, script conventions.
- Memory -> compact durable preferences that should steer future sessions immediately.
- Skills -> reusable procedures and task-class workflows.
- Artifacts -> task outputs and audit trail.

Do not put secrets into `Hermes/Config`.

## Observed voice config pattern from this session

- STT: local faster-whisper base -> free/local compute when installed.
- TTS: Edge TTS -> no per-call API charge, uses Microsoft external service, MP3-capable.
- Gemini TTS config may exist but is not necessarily active. Verify live config before claiming provider/cost.
