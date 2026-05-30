# Media Library Precheck and Typed Routing — 2026-05-27

## Trigger

Use this reference when Xan asks to add a mixed batch of movies and shows, or when torrent automation might confuse Movies and Shows.

## Durable lessons

- Do not rely on filename/title inference as the primary media-type classifier. Agent-added torrents should carry an explicit type/category:
  - movies: `--type movie`, qBittorrent category `movie`
  - shows: `--type show`, qBittorrent category `tv`
  - music: `--type music`, qBittorrent category `music`
- qBittorrent show hooks should only register/process `media_type=show`; movies and music must be skipped rather than guessed.
- Manual qBittorrent adds should set category in the UI. If category is absent, fallback to root path (`D:\Movies`, `D:\Shows`, `D:\Music`); if both are ambiguous, skip automation.
- For mixed requested batches, run a precheck before adding anything:
  1. Query qBittorrent for matching active torrents.
  2. Verify requested movie folders are absent/present as expected.
  3. Verify every requested show folder exists exactly once under `D:\Shows`.
  4. Treat empty show folders as existing-but-empty, not as already acquired.
  5. Scan requested show folders for duplicate episode codes before adding gap-fills.
  6. Scan movie root for normalized duplicate folder suspects before adding/replacing.
- Reject wrong-title indexer bait even when it has high seeders. Example: `The Bear S04` matched `The Island With Bear Grylls`; this must not be added.
- When indexer results are low-seed, future-looking, or weird full packs, present uncertainty or continue with individual episode searches; do not autopilot.

## Duplicate policy reminder

- Duplicate episode code is a review signal, not automatic deletion.
- If destination exists and sizes match, hash before deleting.
- If sizes/quality differ, keep the better candidate only after explicit policy or user approval.
- Preserve collision/review copies rather than overwriting.
