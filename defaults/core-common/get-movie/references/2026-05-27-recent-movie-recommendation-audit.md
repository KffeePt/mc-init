# 2026-05-27 — Recent Movie Recommendation Audit Pattern

## Trigger

Use this when Xan asks for up-to-date movie recommendations not already present in `D:\Movies`, especially alongside a TV gap audit.

## Pattern

1. Scan `D:\Movies` first and normalize local names aggressively: punctuation, dots, release tags, years, and common articles.
2. Build recommendations from a curated recent-release shortlist or a trustworthy metadata source; use torrent/indexer APIs only to check availability/quality, not as the taste/ranking authority.
3. Separate raw availability feeds from the final recommendation list.
4. If a raw feed returns future-looking, low-quality, concert/special, or suspicious entries, label it as polluted and do not present it as the primary list.
5. For each recommendation, include why it fits Xan's existing library/taste and whether local absence was verified.

## Pitfalls

- YTS/listing APIs can return polluted or future-looking entries and are availability-biased. They are useful for checking whether a title has releases; they are not a critic canon and should not drive recommendations alone.
- Fuzzy local matching can falsely exclude a title if a nearby franchise/title exists. If a high-value recommendation seems absent but was excluded, verify manually before dropping it.
- Do not recommend downgrades or duplicates when a 1080p/4K copy is already present.

## Output shape

Recommended artifact files:

- `Curated Movie Recommendations.md`
- `curated_movie_recommendations.json`
- optional raw feed JSON clearly marked as raw/polluted/availability-biased

Recommended chat summary:

- practical shortlist first;
- lower-priority/completionist titles separately;
- mention if raw feeds were distrusted and why.
