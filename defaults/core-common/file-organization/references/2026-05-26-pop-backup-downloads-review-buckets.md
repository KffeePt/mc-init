# 2026-05-26 — POP Backup Downloads Marking and Review Buckets

## Trigger

Use this pattern when cleaning a stale backup tree where a prior manifest already identified review-required files and the user asks to classify a subset, mark removal candidates, and preserve a named bucket such as server backups.

## Pattern

1. **Start from the latest manifest, not a blind rescan.**
   - If a recent `Final Remaining Review Manifest.csv` exists, parse it and create a derived marked manifest.
   - Preserve original columns and append new action/risk/category columns rather than destroying provenance.

2. **Mark, do not delete, when the user asks for review classification.**
   - Use `delete_after_explicit_approval` for candidates.
   - Report clearly that no files were moved or deleted.
   - Make the next deletion pass target a CSV manifest, not fuzzy folder names.

3. **Downloads installer/runtime classification.**
   Mark these as installer/runtime removal candidates when found in stale backed-up Downloads:
   - package extensions: `.exe`, `.msi`, `.msix`, `.appx`, `.deb`, `.rpm`, `.dmg`, `.pkg`, `.appimage`, `.flatpakref`
   - installer/bootstrap scripts: names like `miniconda.sh`, `install_houdini_launcher.sh`, or obvious `install*` shell scripts
   - Java installer JARs: names containing `installer`, e.g. Forge/Iris installers
   - runtime/app archives: names containing `jdk`, `jre`, `openjdk`, `java`, `node`, `postman`, `zen`, or similar runtime/app package terms inside archive extensions such as `.tar.gz`, `.tgz`, `.tar.xz`, `.tar.bz2`, `.zip`, `.7z`, `.rar`

4. **Do not collapse extracted payloads into installer deletion automatically.**
   - Extracted JDK, Postman, Zen, and similar app/runtime folders may be disposable, but they are a different class than installer files.
   - Put them in `extracted_application_payload_review` or broad review unless the user explicitly approves payload cleanup.

5. **Preserve explicit keep buckets across all review classes.**
   - If the user says to keep server backups, mark all matching rows `keep_server_backup`, even if they appear under archive/log review, broad review, or media review.
   - Do not allow size-pressure cleanup to override that instruction.

6. **Sensitive-looking tiny files stay review-required.**
   - Files named like `client_secret*.json`, backup codes, auth exports, key material, or credentials should not be deleted just because they are small or in Downloads.
   - Report metadata only unless asked to inspect contents.

## Artifact shape

Create a timestamped artifact folder containing:

- Markdown report with summary, Downloads child clusters, installer candidates, non-installer review categories, and review-bucket details.
- `Downloads Installer Removal Candidates.csv` — the exact next deletion target if approved.
- `Downloads Detailed Inventory.csv` — full Downloads classification.
- `Marked Review Manifest.csv` — full manifest with appended action/category/risk fields.
- `Review Bucket Detail.csv` — counts/bytes/actions/top folders/extensions per review bucket.
- `Summary.json` — machine-readable counts.
- Optional Telegram-visible PNG summary plus ZIP bundle.

## Session outcome snapshot

In the POP-backup run, the remaining review set was 23,335 files / 8.1070 GiB. Downloads was 1,002 files / 6.7181 GiB. The installer/runtime package mark pass identified 15 files / 0.8757 GiB for `delete_after_explicit_approval`. Minecraft/server backups were explicitly preserved: 21,621 files / 0.7439 GiB.

## Pitfalls

- Do not call non-exact duplicate candidates safe deletes after a hash pass says they are not exact duplicate extras.
- Do not delete extracted app payloads in the same pass as installer files unless the user explicitly broadens approval.
- Do not treat personal media as trash based on path alone.
- Do not bury the user's keep instruction inside the report; propagate it into the marked manifest so future deletion passes respect it.
