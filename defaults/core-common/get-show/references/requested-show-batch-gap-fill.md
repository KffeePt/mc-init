# Requested show batch gap-fill workflow

Use this when Xan gives a list of shows/seasons and then says to download all missing shows.

## Durable lessons

1. Treat the first pass as a gap audit, not an add operation. Verify local folders, existing seasons/episodes, duplicates, and active qBittorrent items before adding anything.
2. If Xan then explicitly says to download every show from the list, proceed without asking again, but only add candidates that pass exact-title validation.
3. For each requested show, summarize what is actually missing before or while adding:
   - existing-but-empty folder
   - present seasons
   - missing seasons/episodes
   - duplicate episode codes already present
4. Short/common titles require stricter validation. Reject high-seed wrong-title bait even when it contains the requested token.
   - `The Bear` search can return Bear Grylls / unrelated bear titles.
   - `Dark S01E##` search can return Dark Matter, Dark Gathering, The Terminal List: Dark Wolf, etc.
5. If individual episode searches for a short/common title return wrong-title bait, prefer an exact season pack query with year/source terms, e.g. `Dark Season 1 2017 1080p NF WEB-DL`, instead of accepting loose false positives.
6. If no clean season-only pack exists but a full-series pack covers the missing target, adding the full pack is acceptable only if the overlap risk is explicitly recorded for post-download cleanup.
7. For full packs that overlap existing content, record cleanup obligations immediately:
   - keep existing files until the new pack completes and verifies
   - compare coverage/quality before deleting old files
   - expect duplicate episodes until flatten/dedup runs
8. Always add show torrents with explicit `--type show` / qBittorrent category `tv` and destination under `D:\Shows\<Show Title (Year)>\`.
9. After adding, verify via qBittorrent API that each torrent has category `tv` and the expected save path; do not trust add success alone.
10. Watcher batches should be expected per destination/show. Long low-seed torrents can delay batch flattening because the hook defers until active show operations finish.

## Reporting shape

Use a compact per-show report:

```text
<Show>
- local: S1-S3 present / empty / duplicate S07E03
- missing: S4 / S1-S6 / S09E01
- added: exact release or pack scope
- risk: overlaps existing content / low seeds / cleanup needed
```

Then provide live qBittorrent state and remaining work:
- wait for completion
- flatten and scan
- Plex refresh
- cleanup overlaps/duplicates
