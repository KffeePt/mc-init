# Telegram manual TTS discipline — 2026-05-22

## Trigger

Xan asked why TTS messages had stopped appearing after a response was sent as text only.

## Observed pattern

- Telegram `tts` toolset can be enabled while `voice.auto_tts` is still `false`.
- In that mode, Hermes does not automatically synthesize every reply.
- The agent must explicitly call the TTS tool and include the returned `MEDIA:/...mp3` path in the final response.
- A text-only final answer after the user expects voice feels like the voice feature was lost, even when config is healthy.

## Operational rule

For simple Telegram replies where Xan expects voice, or after any complaint about missing voice/TTS:

1. Write a short spoken version that avoids literal filenames, commands, URLs, and paths unless necessary.
2. Call the TTS tool before finalizing.
3. Include the returned `MEDIA:` MP3 attachment first or near the top.
4. Include compact text fallback below it.

## Pitfall

Do not say “I’ll send voice next time” without generating audio now. Tool-use enforcement applies here: if voice is promised, produce the MP3 in the same turn.
