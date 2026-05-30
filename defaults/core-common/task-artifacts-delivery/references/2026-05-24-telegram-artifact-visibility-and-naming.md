# Telegram Artifact Visibility and Naming — 2026-05-24

## Session Learning

Artifact delivery over Telegram needs two layers:

1. **Canonical storage** in the shared Hermes artifact workspace.
2. **Transport-safe delivery** as a native Telegram file attachment.

A readable path in the final text is not enough. A ZIP by itself is also not enough when the user needs to understand contents without opening it.

## Rules Added

- Always use `MEDIA:/absolute/path` for files Xan should receive in Telegram.
- For ZIPs or multi-file bundles, attach a readable Markdown companion summary first.
- Name companion summaries with lowercase hyphen slugs:

```text
<task-slug>-summary.md
<dream-slug>-summary.md
```

- Avoid space-heavy delivery filenames. Human-readable folders can keep spaces; the delivered copy should be slugged.
- If final-response `MEDIA:` does not arrive/open, resend with the messaging tool directly using a clean delivery copy.

## Example

Canonical artifact folder:

```text
/mnt/c/Users/santi/Documents/Hermes/Artifacts/2026-05-24/06-25-08/telegram-artifact-test/
```

Delivery file:

```text
/tmp/hermes-artifact-test/telegram-artifact-test-summary.md
```

Delivery message:

```text
MEDIA:/tmp/hermes-artifact-test/telegram-artifact-test-summary.md
```

## Pitfall

Pretty title-case filenames with spaces are readable to humans but less reliable as transport artifacts. Keep pretty folder names if useful, but deliver slug filenames.
