# Telegram Artifact Visibility and Naming — 2026-05-24

## Trigger

Xan corrected artifact delivery repeatedly during a Telegram session:

- A path alone is not delivery.
- ZIPs are acceptable for large/detailed artifacts, but they need a directly readable summary outside the archive.
- The summary should be Markdown, not generic `.txt`.
- The summary filename should be a task/dream slug, not `Artifact Summary`.
- Delivered filenames should be Telegram-safe: lowercase ASCII, hyphens, no spaces.
- If the normal final-response `MEDIA:` path does not arrive/open, resend with the messaging tool directly.

## Durable Rule

For generated artifacts in Telegram:

1. Keep canonical files under the shared artifact workspace.
2. Create a directly readable Markdown summary for any ZIP or multi-file bundle.
3. Name companion summaries as:

```text
<task-slug>-summary.md
<dream-slug>-summary.md
```

4. For delivery, prefer a clean slug delivery copy if the canonical path has spaces or unusual characters:

```text
/tmp/hermes-artifact-test/<task-slug>-summary.md
```

5. Attach with `MEDIA:`. If final response delivery fails or Xan reports not receiving/opening it, resend via:

```text
send_message(action="send", target="telegram", message="MEDIA:/absolute/path/to/<task-slug>-summary.md")
```

## What Not To Do

- Do not send only a Windows/WSL path.
- Do not send only a ZIP without a visible companion summary.
- Do not use generic `Artifact Summary.txt` unless Xan explicitly requests plain text.
- Do not repeatedly send the same space-heavy path if Telegram fails to deliver/open it.

## Verification

Before claiming success:

- Confirm the file exists and is nonzero size.
- Confirm the delivery copy exists if one was made.
- If using direct messaging delivery, record the send result/message ID in the text summary when useful.
