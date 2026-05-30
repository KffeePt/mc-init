# Telegram artifact PNG + audio paired summary

## Session signal
Xan clarified the preferred artifact-delivery experience for Telegram after testing multiple formats:

- `.txt` / `.md` files were not visible/openable enough in-chat.
- PNG image summaries worked and should be the default visible artifact format.
- The PNG and audio/TTS should be correlated: one visual summary plus one spoken version of the same summary.

## Durable delivery convention
For ZIPs, large reports, multi-file artifacts, and detailed task handoffs:

1. Canonical artifacts still live under `Documents/Hermes/Artifacts/...`.
2. Create a Telegram-visible PNG summary:
   - `<task-slug>-summary.png`
   - or `<dream-slug>-summary.png`
3. Create a matching MP3 summary:
   - `<task-slug>-summary.mp3`
   - or `<dream-slug>-summary.mp3`
4. The PNG and MP3 must describe the same content: scope, result, caveat/risk, and remaining work.
5. Attach PNG first/near the bundle and MP3 last when practical.
6. Use text-file summaries only on explicit request.

## Rationale
Telegram native photo display gives immediate visibility. The MP3 gives the same summary in listenable form. Text documents are still useful as canonical artifacts, but not as the primary Telegram visibility layer for Xan.