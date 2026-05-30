# Telegram Artifact Visibility Correction — 2026-05-24

## Session Signal

Xan corrected artifact delivery twice:

1. Files must be attached in Telegram as native `MEDIA:` files, not merely listed as local paths.
2. ZIP bundles need a directly readable `.txt` or `.md` companion summary so their contents are visible without downloading/opening the archive.

## Durable Delivery Pattern

For substantial artifacts:

```text
Attached:
- Visible artifact summary
  MEDIA:/.../Artifact Summary.txt
- Full bundle
  MEDIA:/.../Artifact Bundle.zip
```

For single files:

```text
MEDIA:/absolute/path/to/file
```

## Companion Summary Contents

The summary should include:

- purpose of the artifact/bundle
- included files and their roles
- verification performed
- caveats/limits
- remaining work

## Storage vs Delivery

Paths under `Documents/Hermes/Artifacts` are storage. Telegram `MEDIA:` attachments are delivery. Do both when needed; never confuse one for the other.