---
name: task-artifacts-delivery
description: "Use when producing user-facing plans, walkthroughs, reports, summaries, generated files, or media artifacts that need organized storage and clean delivery back to Xan."
version: 1.0.0
author: Wilson / Hermes Agent
license: MIT
platforms: [windows, wsl, linux]
metadata:
  hermes:
    tags: [artifacts, planning, delivery, telegram, workspace, voice-summary, user-workflow]
    related_skills: [hermes-agent]
---

# Task Artifacts & Delivery

## Overview

Use this skill whenever a task produces durable material for Xan: plans, walkthroughs, audits, reports, exports, generated notes, manifests, summaries, or media. The goal is simple: keep the shared user-AI workspace clean, make outputs easy to find later, and do not clutter Desktop.

This skill is about delivery hygiene, not content generation. The work can be code, ops, research, cleanup, media, or planning. If it creates durable files for the user, this skill applies.

## Core Rules

1. **Use the shared artifact workspace.**

   Windows path:

   ```text
   C:\Users\santi\Documents\Hermes\Artifacts\YYYY-MM-DD\HH-MM-SS\<Pascal Case Purpose>\
   ```

   WSL path:

   ```text
   /mnt/c/Users/santi/Documents/Hermes/Artifacts/YYYY-MM-DD/HH-MM-SS/<Pascal Case Purpose>/
   ```

   Use readable space-separated names for user-facing purpose folders and files under `Documents/Hermes` unless a technical format requires otherwise. Avoid underscores in user-facing artifact names.

2. **Do not put new plans or artifacts on Desktop.**

   If a previous artifact already exists on Desktop, do not move/delete it unless Xan explicitly approves. Copy or migrate it only after approval.

3. **Use timestamped task folders.**

   Every task gets a new timestamp folder. Avoid dumping loose files directly under `Artifacts`.

4. **Use clear PascalCase purpose folders.**

   Suggested folder names:

   - `Plans/`
   - `Walkthroughs/`
   - `Reports/`
   - `Audits/`
   - `Manifests/`
   - `Summaries/`
   - `Exports/`
   - `Media/`
   - `Skills/`
   - `Scripts/`

   Reusable helper scripts and one-time scripts worth keeping belong under:

   ```text
   C:\Users\santi\Documents\Hermes\Scripts\<ScriptPurpose>.<ext>
   ```

   Each saved script should include a short header with purpose, date, inputs, side effects, and safety notes.

5. **Final reply should include the important paths.**

   Give both Windows and WSL paths when useful. Telegram users usually need the Windows path for human navigation and the `MEDIA:` path for native delivery.

## Planning Flow

Before multi-step or file/system-changing work, show Xan a concise plan summary unless he explicitly says `skip plan` or equivalent.

Plan summary should include:

- scope
- intended changes
- affected paths
- risks
- approval needed

Read-only checks and tiny safe actions can proceed directly, then summarize.

Do not make the plan verbose. Xan wants enough to know what will happen, not a committee transcript.

## Artifact Visualization Policy

When an artifact includes charts, reports, visual summaries, scan output, or any value relationship visualization, follow Xan's current chart preference:

- **One primary chart by default.** Do not attach multiple charts unless Xan asks for multiple views or the artifact type genuinely requires separate visual panels.
- **Prefer pie/donut charts for general visualization.** Use them for composition, share-of-total, storage breakdowns, cleanup buckets, media-type shares, and top-folder summaries.
- **Use bar charts only for comparison/ranking.** Bar charts are acceptable when comparing specific items, ordering candidates, or showing ranked differences. Do not use them as the default “visualization” chart.
- **Graph relationships between values.** If describing a relationship among one or more values — trend, overlap, before/after movement, correlation, dependency, rate, or change over time — include a programmatic graph rather than prose alone.
- **Render factual charts programmatically.** Use Python/matplotlib/Pillow/SVG or equivalent deterministic code. Do not use NanoBanana or image-generation models for factual charts or arithmetic-bearing visuals.
- **NanoBanana scope:** use NanoBanana only for explainer infographics or presentation-style visuals, and only when Xan explicitly requests that style.
- **Delivery:** for Telegram, attach the single primary chart with `MEDIA:` when useful; list secondary chart paths as plain text only if they exist and are not central.

## Response Style for Artifacts

Xan prefers concise, high-signal text that is clear, not cryptic. Avoid over-compressed “caveman” phrasing when clarity suffers.

Use this shape by default unless Xan requests a different format:

```text
Plan
- ...

Clarification Questions
- None needed.  # omit unless ambiguity cannot be verified with tools

Tools
- ...

Work Done
- ...

Remaining Work / Technical Debt
- ...

TTS summary
- ...

TTS audio / artifacts
- MEDIA:/absolute/path/to/audio-or-artifact
```

For very small replies, keep the same order but collapse empty sections. Prefer compact bullets, short labels, and `->` for source/destination or flow. Drop sections that add no value.

When tasks, issues, review items, unknown scan areas, skipped items, or next actions remain unresolved, include a `Remaining work:` section in the text response. If a prior turn already listed unresolved work and the current turn does not remediate it, carry that prior work forward instead of saying none. If nothing remains, say so briefly rather than leaving the operator to infer completion. Mirror the same remaining-work status in the audio summary using listener-safe wording; avoid literal paths/filenames in audio unless explicitly requested.

## User-Facing Communication Style

Use this response style whenever handing off artifacts, summaries, plans, status reports, or TTS text to Xan:

1. **English default.** Answer in English even when Xan writes or speaks Spanish, Spanglish, or another language, unless he explicitly asks for a different language.
2. **Voice/STT language is not output language.** A Spanish or mixed-language voice transcription is still answered in English by default; do not mirror transcript language just because STT produced it.
3. **Requested language overrides default.** If Xan explicitly asks for Spanish or another language, use that language for the main response and matching TTS text.
4. **Voice accent is provider config.** The agent controls the text/language sent to TTS; the actual accent/voice comes from Hermes TTS provider config. If Xan complains about a wrong accent, separate content-language fixes from provider configuration.
5. **Tone.** Direct, skeptical, technically precise, anti-sycophantic. No fake corporate warmth, no therapy tone, no emojis unless Xan asks.
6. **Do not over-narrate.** Keep final replies compact and operational. Exact paths, commands, IDs, and artifacts belong in text, not spoken TTS unless requested.

For long responses, include a short plain `TTS summary:` and generate audio for that summary only when TTS is available. Spoken summaries should usually be 2–5 sentences and avoid exact filenames, URLs, hashes, IDs, commands, and long paths.

## Voice Summary Delivery

Xan expects **every assistant response** to include a Telegram-compatible MP3, audio-friendly summary, regardless of whether the task was simple, long, technical, operational, or artifact-producing. Do not limit voice delivery to “straightforward” replies. Always include a compact text fallback as well so the answer works when audio cannot be heard.

**Manual TTS discipline:** if `voice.auto_tts` is disabled, Hermes will not automatically convert replies to voice. Even if `voice.auto_tts` is enabled, when operating from Telegram and a final response is being composed, prefer explicitly calling the TTS tool before finalizing and include the returned `MEDIA:` MP3 path. Do not merely say that voice will be sent. Generate it in the same turn.

When the task is long or highly technical, the voice summary should be short and listener-safe: outcome, key risk, and next action. Do not read literal filenames, URLs, long commands, code blocks, or exact paths aloud unless Xan explicitly asks; keep exact strings in text.

Preferred format for Telegram delivery:

```text
.mp3
```

Avoid `.wav` for Telegram unless specifically requested; it may not play cleanly in-chat.

Recommended voice defaults for cheap/reliable operation:

- **TTS:** Edge TTS (`tts.provider: edge`) — free, no API credits, direct MP3 output.
- **STT:** local faster-whisper (`stt.provider: local`, `stt.local.model: base`) — free/local when installed.

Config shape:

```yaml
tts:
  provider: edge

stt:
  enabled: true
  provider: local
  local:
    model: base
```

If a premium/cloud TTS provider fails due to credits or quota, regenerate the same summary with Edge TTS rather than leaving the user with unusable audio.

## Telegram Media Delivery

For media files, include a native media attachment path in the final response:

```text
MEDIA:/absolute/path/to/file.mp3
```

For images/videos/audio, prefer native delivery over a plain path when the platform supports it.

For ZIPs or large/multi-file bundles, always attach a correlated PNG + audio companion summary pair first/last. Name both with the same Telegram-safe lowercase hyphen task/dream slug, and attach exactly one delivery copy of each media artifact:

```text
MEDIA:/tmp/hermes-artifact-delivery/task-slug-summary.png
MEDIA:/tmp/hermes-artifact-delivery/task-slug-bundle.zip
MEDIA:/tmp/hermes-artifact-delivery/task-slug-summary.mp3
```

Do not also attach canonical archive copies from `Documents/Hermes/Artifacts/...`; list those canonical paths as plain text if useful. The PNG companion summary should explain the bundle contents, purpose, verification, caveats, and remaining work so Xan has visibility in Telegram without downloading/opening the archive. The MP3 should be the short spoken version of the same content: same scope, same outcome, same caveat, same remaining work. Use `.md` or `.txt` only if Xan explicitly asks.

## Configuration Storage Policy

Use the right persistence layer:

- Native Hermes runtime settings -> `~/.hermes/config.yaml` via `hermes config set` / `hermes config edit`.
- Shared user-facing operating policy -> `C:\Users\santi\Documents\Hermes\Config\*.yaml`.
- Compact durable preferences -> memory.
- Reusable procedures -> skills.
- Session/task outputs -> `Hermes/Artifacts/...`.

Do not put secrets in `Hermes/Config`; use `.env` or Hermes auth stores.

## STATE.md Operational Ledger

For tool-heavy runs, memory writes, file patches, config edits, skills/plugins changes, scheduled-task edits, or multi-step investigations, maintain a reusable `STATE.md` ledger in the shared Hermes workspace.

Recommended Windows path:

```text
C:\Users\santi\Documents\Hermes\STATE.md
```

Recommended WSL path:

```text
/mnt/c/Users/santi/Documents/Hermes/STATE.md
```

Each entry should be concise but auditable:

- timestamp
- intent/request
- tools/actions used
- files touched
- memory/skill/config/scheduler changes
- decisions and safety gates
- verification performed
- risks/anomalies
- remaining work

Do not dump raw logs unless the log excerpt is needed to understand the decision. Summarize with enough detail for a later agent to resume safely.

If a run is blocked by an approval timeout or another safety gate, record the partial state before final response when file tools are available. If file tools are not available, state the missing ledger update explicitly in the final handoff.

## Artifact Creation Checklist

- [ ] STATE.md updated for tool-heavy, config-changing, scheduled-task, skill/memory, or multi-step investigation work
- [ ] Chosen timestamp path under `Documents/Hermes/Artifacts`
- [ ] PascalCase purpose subfolder created
- [ ] Desktop untouched unless approved
- [ ] Text summary/report saved if durable
- [ ] If sending a ZIP or multi-file bundle, correlated PNG + audio companion summary pair named `<task-slug>-summary.png` and `<task-slug>-summary.mp3` created
- [ ] If charts are included, one primary programmatic pie/donut is attached by default; bar charts appear only for explicit comparison/ranking; relationships are graphed programmatically
- [ ] NanoBanana was not used for factual charts; it is only used for requested explainer infographics
- [ ] Exactly one delivery copy of each media artifact attached as `MEDIA:`; canonical archive paths listed as text only unless Xan asks for duplicate attachments
- [ ] Compact text fallback included for simple voice replies
- [ ] If TTS is expected and `auto_tts` may be off, explicitly generated MP3 before final response
- [ ] MP3 summary saved when useful and feasible
- [ ] Scripts saved under `Hermes/Scripts/<ScriptPurpose>.<ext>` when worth keeping
- [ ] Final response includes relevant paths
- [ ] Final response includes `MEDIA:` for deliverable media
- [ ] Verified file exists and has nonzero size when possible

## Common Pitfalls

1. **Stopping after a safety/approval interruption without recording state.** If a multi-step operational run is blocked by a destructive-action approval timeout or similar safety gate, update the normal response with exact remaining work and record the partial state in `STATE.md` before ending. The next run needs to know what was changed, what was verified, and what cleanup remains.
2. **Writing plans to Desktop.** Do not. Desktop is not the artifact workspace.
2. **Creating loose files directly in Documents.** Use the timestamped `Artifacts` hierarchy.
3. **Using old lowercase `.artifacts` paths.** Current workspace uses `Hermes/Artifacts` and PascalCase names.
4. **Making plans too long.** The plan should give control and risk visibility, not drown the user.
5. **Sending only audio for simple replies.** Always include compact text fallback.
6. **Delivering WAV to Telegram.** Use MP3 unless Xan asks otherwise.
7. **Claiming a file exists without verification.** Read/stat it or use the tool result before stating success.
8. **Moving old Desktop files without permission.** Copy/move/delete only after explicit approval.
9. **Stuffing user workflow policy into native Hermes config.** Use native config for runtime settings; use `Hermes/Config/*.yaml`, memory, or skills for operating policy.
10. **Sending mismatched PNG and audio summaries.** For artifact delivery, visual and spoken summaries must be correlated: same scope, same outcome, same caveat, same remaining work.
11. **Using bar charts as default visuals.** Xan prefers pie/donut charts for general visualization and bars only for comparison/ranking.
12. **Using NanoBanana for factual charts.** Factual charts must be programmatic; NanoBanana is only for requested explainer/presentation infographics.
13. **Describing value relationships without graphing them.** If the relationship matters, graph it programmatically.

## Reference Material

- `references/2026-05-22-user-artifact-and-voice-preferences.md` captures the original session-specific correction that created this workflow.
- `references/2026-05-22-workspace-voice-config-corrections.md` captures later corrections: PascalCase `Hermes/Artifacts`, `Hermes/Scripts`, simple voice replies with text fallback, and config-vs-memory policy.
- `references/2026-05-26-qbittorrent-hook-scripts-hermes-workspace.md` captures the qBittorrent/Plex hook script location correction: durable shared automation scripts should move from ad-hoc drive script folders into `Hermes\Scripts`, with qBittorrent commands and related skills updated together.
- `references/2026-05-22-telegram-manual-tts-discipline.md` captures the manual-TTS failure mode when `voice.auto_tts` is off and the agent must explicitly generate an MP3 before finalizing.
- `references/2026-05-22-telegram-all-responses-tts-correction.md` captures Xan's correction that every Telegram response should include a short MP3 audio-friendly summary, no matter how long or technical the task.
- `references/2026-05-24-telegram-artifact-png-audio-pair.md` captures the final Telegram artifact convention: default paired PNG visual summary plus matching MP3 audio summary, both generated from the same content spine.
- `references/2026-05-24-telegram-artifact-visibility-and-naming.md` captures earlier Telegram artifact corrections: native `MEDIA:` attachments, visible companion summaries, and clean slug filenames.
