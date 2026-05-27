# Telegram ZIP Visible Summary Correction — 2026-05-24

## Session Signal

Xan clarified that ZIP bundles are useful for large/detailed artifacts, but they are insufficient for Telegram visibility. He needs a directly openable `.txt` or `.md` companion summary attached in-chat so he can understand the bundle contents without downloading or opening the archive.

## Durable Rule

When delivering a ZIP or multi-file artifact bundle:

1. Create a concise visible companion summary: `Artifact Summary.txt` preferred, `.md` acceptable.
2. Attach the summary via `MEDIA:` before or alongside the ZIP.
3. The summary must include:
   - what the bundle contains
   - why major files exist
   - verification status
   - caveats/risks
   - remaining work
4. Then attach the ZIP/bundle if useful.

## Why This Matters

A ZIP is storage, not visibility. Telegram users may be mobile, may not want to download, or may need a quick audit before opening an archive. The companion summary is the legible surface.

## Correct Response Shape

```text
Attached:
- Visible artifact summary
  MEDIA:/.../Artifact Summary.txt
- Full artifact bundle
  MEDIA:/.../Artifact Bundle.zip
```

## Pitfall

Do not treat the chat message summary alone as sufficient when a ZIP is attached. The companion summary should be an actual file so it remains durable and directly visible as an artifact.