# 2026-05-26 MAMBA → BIGGIE Cross-Drive Episode Comparison

Session-specific reference for the `storage-explorer` umbrella skill. Use this as a concrete pattern when Xan asks to verify whether one media library has been fully copied to another.

## Context

Xan asked to verify whether all MAMBA (F:\Shows) media was properly copied to BIGGIE Archived (D:\Archived Shows + D:\Archied Shows), and to check for OBS recordings.

## Technique: Three-Pass Comparison

### Pass 1 — Show-Level (fast, ~10 seconds)

```powershell
# Collect show name, file count, total bytes, top extensions per show
Get-ChildItem -LiteralPath $root -Directory | ForEach-Object {
    $files = Get-ChildItem -LiteralPath $_.FullName -Recurse -File
    [pscustomobject]@{ Show=$_.Name; Files=$files.Count; TotalBytes=($files | Measure-Object Length -Sum).Sum }
}
```

Compare show names between MAMBA and Archived. Identify:
- Shows present in both
- Shows missing from Archived (needs copy)
- Extra shows in Archived (already archived, fine)

### Pass 2 — Episode-Level (fast, ~5 seconds for 5,376 episodes)

```powershell
# Build episode map: show_name -> {episode_key_lower -> file_info}
# Match by filename (case-insensitive), compare sizes
# This catches: missing episodes, size mismatches
# Output: Show Comparison.csv, Episode Mismatches.csv
```

Match every video file by lowercase filename. Compare sizes. Only flag size mismatches for hash verification — don't hash everything.

### Pass 3 — Hash Verification (only when needed)

Only hash files where:
- Sizes differ but names match (possible re-encode)
- User demands cryptographic certainty
- Use stratified random sampling, not exhaustive hashing

## Key Findings From This Session

- 80 shows present in both, 5,376 episodes matched by name
- All 5,376 matched episodes had **identical sizes** — zero size mismatches
- 169 episodes missing from BIGGIE Archived across 8 shows:

| Show | MAMBA Eps | Archived Eps | Missing | Missing From |
|---|---|---|---|---|
| The-Boys | 69 | 0 | 69 | Entire show (S1 mp4, S2-S4 mkv, featurettes) |
| The Expanse S1-S6 | 61 | 24 | 37 | S3 (10), S4 (10), S5 (10), S6 (6) |
| The-Bear | 28 | 8 | 20 | S2 (10), S3 (10) |
| Love-Death-And-Robots | 28 | 18 | 10 | S4 (10) |
| Severance | 19 | 9 | 10 | S2 (10) |
| Fallout | 16 | 8 | 8 | S2 (8) |
| Stranger-Things | 42 | 34 | 8 | S5 (8) |
| The-Last-of-Us | 16 | 9 | 7 | S2 (7) |

- Estimated missing data: ~230-270 GiB. The-Boys alone is ~110-130 GiB.
- 4 extra shows on Archived only (normal archive drift): Aqui no hay quien viva, Malcolm in the Middle, The-Wolf-of-God, Yellowstone.
- Stratified hash sample: 30/209 verified with SHA-256, all matched. Sampling in progress at session end.

## Pitfalls

1. **Exhaustive SHA-256 across 5,000+ episodes on spinning disk = ~36 hours.** Don't do it. Use size comparison for the bulk, hash only size mismatches, or use stratified sampling for confidence.

2. **WSL-launched Windows processes are I/O-throttled for large file reads.** Even native Windows Python launched via `powershell.exe` or `cmd.exe` from WSL reads at ~26 MB/s instead of 100-150 MB/s. Use `cmd.exe /c start` to fully detach, or accept the slower rate for background jobs.

3. **The-Boys had zero episodes in Archived.** Always check for shows that are completely absent, not just shows with missing newer seasons. A show with 0 archived episodes is a bigger gap than one missing its latest season.

4. **Two concurrent Python hash processes on the same physical disk thrash the read heads.** Kill stragglers from prior runs before launching a new hash/scan job. The progress stall from 20→30 took 5+ minutes when both the old exhaustive hash and the new sample process were fighting for D:/F:.

## Scripts Created

- `CompareMambaBiggieEpisodes.ps1` — show-level + episode-level PowerShell comparison
- `HashAllMambaBiggieEpisodes.ps1` — parallel SHA-256 (too slow via WSL; use sampling instead)
- `verify_mamba_biggie_hashes.py` — native Windows Python hasher (still I/O-bound via WSL launch)

## Artifact Pattern

```
Artifacts/YYYY-MM-DD/HH-MM-SS/Mamba Biggie Episode Hash Comparison/
  Show Comparison.csv
  Episode Mismatches.csv
  Comparison Summary.json
```
