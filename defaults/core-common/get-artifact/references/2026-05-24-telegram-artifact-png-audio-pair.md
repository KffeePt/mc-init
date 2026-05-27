# Telegram artifact PNG + audio paired summary

## Session signal
Xan tested `.txt` and `.md` artifact summaries in Telegram and reported they were not visible/openable enough. A PNG image summary did render correctly. He then corrected the workflow again: the PNG image and the TTS/audio should be correlated, forming one summary pair rather than independent outputs.

## Durable rule
For large artifacts, ZIP bundles, or detailed deliveries in Telegram:

1. Create a PNG visual summary by default.
2. Create a short MP3/TTS summary from the same content spine.
3. Use the same task/dream slug for both files:
   - `<task-slug>-summary.png`
   - `<task-slug>-summary.mp3`
4. The PNG and audio must share:
   - scope
   - key outcome
   - caveat/risk
   - remaining work
5. Send the PNG as the visual scan surface and the MP3 as the spoken version.
6. Use `.md`/`.txt` only when Xan explicitly asks for text-file delivery.

## Why
Telegram document/file handling was unreliable for `.txt`/`.md` in this context. PNG appeared directly and gave visibility. The audio helps when visual scanning is inconvenient, but it must not drift from the PNG summary.

## Pitfall
Do not send a PNG summary with one set of facts and a TTS summary with another. That creates two sources of truth. Produce both from the same bullet list.