---
name: get-artifact
description: Use when Xan asks to see, get, open, receive, deliver, resend, package, or retrieve any generated file/artifact in Telegram or another messaging conversation. Centralizes artifact lookup, verification, packaging, and native MEDIA delivery instead of dumping paths the user cannot inspect.
version: 1.0.0
author: Wilson / Hermes Agent
license: MIT
platforms: [windows, wsl, linux]
metadata:
  hermes:
    tags: [artifacts, delivery, telegram, files, media, workspace, verification]
    related_skills: [task-artifacts-delivery, hermes-agent]
---

# Get Artifact

## Overview

Use this skill whenever Xan asks for a file/artifact to be sent back in the conversation, or when a task creates durable output that Xan needs to inspect. The failure mode this skill prevents is obvious and stupid: telling him a path exists when Telegram should have received the file as an attachment.

Paths are still useful for auditability. They are not delivery.

## When to Use

Use this skill when Xan says or implies:

- "send it to me as a file"
- "I can't see it"
- "give me the artifact"
- "resend the report"
- "attach the file"
- "send the patch/summary/state/log"
- "where is the artifact?" and the practical answer is a file
- a task generated plans, reports, summaries, scripts, logs, exports, images, audio, video, markdown, JSON, CSV, ZIPs, or any durable output meant for Xan

Also use this skill after file-patching/config/skill work when a patch summary or ledger entry should be visible to Xan from Telegram.

Do **not** use for:

- ephemeral command output that fits cleanly in the message body
- secrets, credentials, tokens, private keys, cookies, raw auth dumps
- destructive moves/deletes unless Xan explicitly approved them

## Core Rule

If Xan needs to inspect a generated artifact from Telegram, the final response must include a native attachment reference:

```text
MEDIA:/absolute/path/to/file
```

A plain Windows path or WSL path is not enough. A Markdown link to a local path is not enough. A promise to send it later is not enough. Attach the file now.

## Delivery Flow

1. **Identify the requested artifact.**
   - Use the explicit path if Xan gave one.
   - If he refers to "it", resolve from the last generated/mentioned artifact in the current task.
   - If ambiguous, search likely locations before asking:
     - `/mnt/c/Users/santi/Documents/Hermes/Artifacts/`
     - `/mnt/c/Users/santi/Documents/Hermes/`
     - `/home/xantastique/.hermes/`
     - current working directory

2. **Verify before claiming.**
   - Confirm the file exists.
   - Confirm nonzero size unless an empty file is expected and explicitly useful.
   - For generated text artifacts, read a small section if needed to make sure it is the right file.

3. **Make it Telegram-friendly.**
   - Prefer the original file as the canonical artifact.
   - For Telegram delivery, create a separate delivery copy when needed:
     - lowercase ASCII filename
     - hyphens instead of spaces
     - short path if possible, e.g. `/tmp/hermes-artifact-test/<task-slug>-summary.md`
     - preserve the original canonical copy under `Documents/Hermes/Artifacts/...`
   - If Telegram preview/attachment handling is unreliable for a format, create a copy with a clearer extension or package it:
     - `.md` -> send directly with a lowercase hyphen slug filename
     - multiple files -> create a `.zip`
     - logs with noisy names -> copy to a readable slug filename first
   - Never rename/move the canonical file just for delivery; copy/package it.

4. **Attach using `MEDIA:`.**
   - Attach **only the Telegram delivery copy** as `MEDIA:`. Do not also attach the canonical archive copy unless Xan explicitly asks.
   - For a paired artifact summary, send exactly one PNG and exactly one MP3. Duplicate visual/audio files are noise, not redundancy.
   - Keep canonical Windows/WSL paths in text for audit/navigation, not as extra `MEDIA:` attachments.
   - Keep the text short: what it is, why it was sent, and any remaining work.
   - If a final-response `MEDIA:` attachment does not arrive or is not openable in Telegram, resend the same delivery copy with `send_message(action="send", target="telegram", message="MEDIA:/absolute/path")`. Do not send both canonical and delivery copies.

5. **For multiple deliverables or ZIP bundles, create correlated PNG + audio summaries by default.**
   - Create a concise PNG image summary named `<task-slug>-summary.png` or `<dream-slug>-summary.png` under the task's artifact folder.
   - Generate a short TTS/audio summary from the same bullet content and name/cache it with the same task/dream slug when possible.
   - The PNG and audio must be correlated: same scope, same key outcome, same caveat, same remaining work. The audio is the spoken version of the PNG, not a separate ramble.
   - Use Telegram-safe slug filenames: lowercase ASCII, hyphens, no spaces.
   - Send the PNG as a native photo via `MEDIA:` and the audio as MP3 via `MEDIA:` so Xan can either look or listen.
   - Do **not** use `.txt` or `.md` for the primary visible summary unless Xan explicitly asks; those failed in Telegram during testing.
   - This summary pair is mandatory when sending a ZIP: Xan needs visibility without downloading/opening the archive.
   - Include what the ZIP contains, why each major file exists, source paths, verification, caveats, and remaining work.
   - Attach the PNG summary before or alongside the ZIP, and attach the matching audio summary last.

6. **For multiple deliverables, create a manifest when useful.**
   - Save a concise `Artifact Manifest.md` under the task's artifact folder when there are several files or audit details.
   - Include file names, purpose, source path, verification, and any caveats.
   - Attach the visible summary plus either all files or a ZIP bundle.

## Packaging Commands

Use tools where possible. When a shell is appropriate:

```bash
# Verify
stat -c '%n %s bytes' /absolute/path/to/file

# Create a zip bundle from a folder
python - <<'PY'
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
src = Path('/absolute/path/to/folder')
out = src.with_suffix('.zip')
with ZipFile(out, 'w', ZIP_DEFLATED) as z:
    for p in src.rglob('*'):
        if p.is_file():
            z.write(p, p.relative_to(src.parent))
print(out)
PY
```

Avoid `cat`/`head` for reading; use `read_file`. Avoid `ls/find/grep`; use `search_files`.

## Response Shape

```text
Attached:
- Visual summary
  MEDIA:/tmp/hermes-artifact-delivery/task-slug-summary.png
- Full artifact bundle
  MEDIA:/tmp/hermes-artifact-delivery/task-slug-bundle.zip
- Matching audio summary
  MEDIA:/tmp/hermes-artifact-delivery/task-slug-summary.mp3

Canonical archive paths:
- PNG: /mnt/c/Users/santi/Documents/Hermes/Artifacts/.../task-slug-summary.png
- MP3: /mnt/c/Users/santi/Documents/Hermes/Artifacts/.../task-slug-summary.mp3

Verified:
- PNG summary exists, <size>
- audio summary exists, <size>
- bundle exists, <size>

Remaining work:
- ...
```

When sending a ZIP or large bundle, attach a correlated PNG + audio summary pair by default. Use the same task/dream slug and the same content spine: `<task-slug>-summary.png` plus `<task-slug>-summary.mp3`. Send exactly one copy of each media artifact: the Telegram delivery copy. Do not also attach canonical archive copies; list canonical paths as plain text if useful. The PNG is for visual scanning; the audio is the short spoken version. They should not contradict each other. Strange that this needs saying, but here we are.

## Interaction With STATE.md

For memory writes, tool-heavy runs, file patches, config edits, skill/plugin changes, or multi-step investigations:

- Append a concise entry to `/mnt/c/Users/santi/Documents/Hermes/STATE.md`.
- If Xan asks to see it, attach the actual `STATE.md` file via `MEDIA:`.
- If the entry generated a patch summary or manifest, attach that too.

## Reference Material

- `references/2026-05-24-telegram-artifact-png-audio-pair.md` captures the final Telegram artifact convention: PNG visual summaries plus matching MP3 audio summaries, correlated from the same content spine.
- `references/2026-05-24-telegram-artifact-visibility-and-naming.md` captures the earlier correction that Telegram artifacts need native `MEDIA:` attachment, clean slug filenames, and sometimes direct `send_message` delivery when final-response attachment delivery is unreliable.
- `references/2026-05-24-telegram-zip-visible-summary.md` captures the intermediate correction that ZIP bundles must be accompanied by a visible summary artifact for visibility without opening the archive.

## Common Pitfalls

1. **Only giving a path.** Xan may not be at the machine. Telegram needs an attachment.
2. **Assuming `MEDIA:` happened when it did not.** Put the literal `MEDIA:/absolute/path` in the final response.
3. **Sending a directory.** Package directories as ZIPs first.
4. **Attaching stale artifacts.** Verify modification time/content when the request is contextual.
5. **Leaking secrets.** Redact or refuse to attach credential material unless explicitly safe and intentional.
6. **Cluttering Desktop.** Use `Documents/Hermes/Artifacts/...`; never dump delivery copies on Desktop.
7. **Over-speaking in TTS.** Voice summary should say what was attached, not recite paths.
8. **Letting PNG and audio drift.** For paired summaries, generate both from the same bullet content. If the PNG says one risk and the MP3 says another, you made two little lies instead of one summary.

## Verification Checklist

- [ ] Correct artifact identified
- [ ] File exists and size checked
- [ ] If sending a ZIP, correlated PNG + audio summary pair named `<task-slug>-summary.png` and `<task-slug>-summary.mp3` created
- [ ] Exactly one delivery copy of each media artifact attached as `MEDIA:`; canonical archive paths listed as text only unless Xan asks for duplicate attachments
- [ ] If multiple files, manifest or ZIP created
- [ ] Final response includes `MEDIA:/absolute/path/to/file` for summary and bundle/file
- [ ] Text says what was attached
- [ ] Remaining work included when relevant
- [ ] STATE.md updated when the run involved memory/config/skill/tool-heavy changes
