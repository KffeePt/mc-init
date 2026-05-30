# Telegram TTS Expectation Correction — 2026-05-22

## Signal

Xan corrected the assistant after a Telegram response omitted speech/TTS behavior from the persistent operating expectations:

> still the speech to text is missing make sure your sysprompt has on it that all the responses should include the tts audio friendly summary no matter how long or technical the task

## Durable lesson

For Telegram delivery, voice is not a “simple replies only” convenience. Xan expects every response to include a Telegram-compatible MP3 audio-friendly summary plus compact text fallback.

## Operational rule

- Generate a short MP3 summary for every final response when the TTS tool is available.
- Keep the voice summary listener-safe: outcome, key risk, next action.
- Avoid speaking literal file paths, commands, URLs, long identifiers, or code unless explicitly requested.
- Put exact technical strings in text, not audio.
- If changing Hermes config, `voice.auto_tts = true` helps future sessions but does not guarantee the current running gateway/session reloads immediately; explicit TTS generation is still safer.

## Related config verified in-session

```yaml
tts:
  provider: edge
stt:
  enabled: true
  provider: local
  local:
    model: base
voice:
  auto_tts: true
```
