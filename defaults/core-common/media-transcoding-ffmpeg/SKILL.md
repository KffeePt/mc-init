---
name: media-transcoding-ffmpeg
description: Use when Xan wants to compress, transcode, test, or batch-process media libraries with FFmpeg while preserving originals and avoiding drive corruption or folder mistakes.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ffmpeg, transcoding, media, plex, storage, windows, wsl]
    related_skills: [personal-server-status-report]
---

# Media Transcoding with FFmpeg

## Overview

This workflow is for Xan's Windows/WSL media server where media drives are mounted under WSL and visible to Windows:

- BIGGIE: currently `D:` / `/mnt/d` — Seagate 8 TB, main safe test/workspace drive. Resolve by label because letters may change.
- MAMBA: currently `F:` / `/mnt/f` — Seagate 4 TB, nearly full media drive. Resolve by label because letters may change.
- BOLT: currently `E:` — additional NTFS volume observed.
- GPU: NVIDIA GeForce GTX 1070 with working `hevc_nvenc` and `h264_nvenc` in FFmpeg 8.1.1.
- FFmpeg install: `C:\Users\santi\Tools\ffmpeg\bin` / `/mnt/c/Users/santi/Tools/ffmpeg/bin`.
- Test transcoder project: `C:\Users\santi\Documents\GitHub\transcoder`.
- Test workspace: `BIGGIE:\HermesTranscoderTest` / currently `/mnt/d/HermesTranscoderTest`.

Prime directive: never modify originals. Copy samples into a test workspace, transcode outputs into a separate folder, probe results, compare size/quality, then decide whether a broader batch is warranted. Batch replacement of originals is forbidden unless Xan explicitly approves a separate destructive migration plan.

## When to Use

Use this skill when Xan asks to:

- compress media to save disk space;
- transcode movies or shows with FFmpeg;
- build or use helper programs for media folders;
- test x265/HEVC settings;
- prepare Plex-friendly versions;
- scan media libraries for codecs, sizes, or candidates.

Do not use it for unrelated media downloads, piracy workflow, or destructive cleanup.

## Safety Rules

1. **Originals are read-only.** Never run FFmpeg output to the same path as input.
2. **Use BIGGIE for tests.** Prefer `D:\HermesTranscoderTest` for imports, outputs, logs, and reports.
3. **Copy before transcode.** Import samples first, then transcode imported copies.
4. **Preserve streams by default.** Use `-map 0 -map_metadata 0 -map_chapters 0`, copy audio/subtitle streams unless a reason exists to re-encode.
5. **Avoid blind batch jobs.** Probe codecs and run sample tests by content type first.
6. **Account for WSL/Windows paths.** Windows `ffmpeg.exe` may reject `/mnt/d/...`; pass `D:\...` paths when invoking the Windows binary.
7. **No automatic deletion.** Even if output is smaller and valid, do not delete source files without explicit approval and a rollback/checksum plan.

## Known Paths

```text
Windows FFmpeg: C:\Users\santi\Tools\ffmpeg\bin\ffmpeg.exe
Windows FFprobe: C:\Users\santi\Tools\ffmpeg\bin\ffprobe.exe
WSL FFmpeg: /mnt/c/Users/santi/Tools/ffmpeg/bin/ffmpeg.exe
WSL FFprobe: /mnt/c/Users/santi/Tools/ffmpeg/bin/ffprobe.exe
Project: /mnt/c/Users/santi/Documents/GitHub/transcoder
Test root: /mnt/d/HermesTranscoderTest
Imports: /mnt/d/HermesTranscoderTest/Imports
Outputs: /mnt/d/HermesTranscoderTest/Outputs
Reports: /mnt/d/HermesTranscoderTest/Reports
Logs: /mnt/d/HermesTranscoderTest/Logs
Desktop launcher: /mnt/c/Users/santi/Desktop/transcoder.bat
```

## Standard Test Flow

1. Verify FFmpeg, labels, and NVENC:

```bash
cd /mnt/c/Users/santi/Documents/GitHub/transcoder
.venv/bin/python main.py selftest
```

2. Map candidates into a JSON plan. This probes codecs, records sizes/streams, and chooses skip/transcode plus encoder/quality per file:

```bash
.venv/bin/python main.py map-files --limit 20 --min-mb 650 --output latest_map.json
```

3. Review the map before running anything:

```bash
python3 -m json.tool /mnt/d/HermesTranscoderTest/Maps/latest_map.json
```

4. Dry-run the map first:

```bash
.venv/bin/python main.py run-transcoding /mnt/d/HermesTranscoderTest/Maps/latest_map.json --dry-run
```

5. Run sample/test workflow when validating settings. It cleans only the RandomSamples/TestRun test folders, copies random samples from BIGGIE/MAMBA, maps them, then transcodes the copies:

```bash
.venv/bin/python main.py run-test --samples 3 --min-mb 50
```

6. Use the TUI for manual operation:

```bash
.venv/bin/python main.py tui
```

Legacy one-file helper behavior is retained via `main.py transcode-one`, but the map/run workflow is preferred for maintainability and auditability.

## Recommended FFmpeg Defaults

For Xan's Plex/archive storage-pressure workflow, the practical default codec is **HEVC / H.265 / x265**, not AV1, unless there is a separate client/hardware compatibility reason to choose otherwise. Keep AV1 as a selective experiment after x265 baselines; it can compress better but is slower and more likely to trigger Plex/client friction.

For high-quality x265 archive copies:

```bash
ffmpeg -hide_banner -i INPUT \
  -map 0 -map_metadata 0 -map_chapters 0 \
  -c:v libx265 -preset slow -crf 22 -pix_fmt yuv420p10le \
  -c:a copy -c:s copy \
  OUTPUT.mkv
```

For faster CPU tests:

```bash
-c:v libx265 -preset medium -crf 23 -pix_fmt yuv420p10le
```

For GPU-accelerated HEVC on Xan's GTX 1070, the transcoder helper now uses `--encoder auto`, selecting `hevc_nvenc` when available and falling back to CPU `libx265`. Verified NVENC settings:

```bash
-c:v hevc_nvenc -preset p5 -tune hq -rc vbr -cq 23 -b:v 0 -pix_fmt p010le
```

NVENC uses CQ rather than x265 CRF; the helper keeps `--crf` as the user-facing numeric quality control. GPU encoding is dramatically faster but may be less space-efficient than CPU x265 at similar perceived quality. Use it for speed-sensitive batches and compare against CPU x265 before committing huge archive migrations.

Use `CRF/CQ 20-22` for higher quality, `23-24` for more savings. Do not apply one value blindly across all media; animation, grain, dark scenes, and older sources behave differently. See `references/codec-selection-plex-archive.md` for the codec decision matrix, observed MPEG2->x265 test result, and audio policy.

## Candidate Selection Heuristics

Good candidates:

- h264/x264 video larger than expected;
- MPEG2/Xvid/AVI older shows;
- 1080p web or bluray files above ~1 GB per 22-minute episode or above ~4 GB per movie;
- duplicate folders across BIGGIE and MAMBA, after checksum confirmation.

Poor candidates:

- already x265/HEVC unless unusually bloated;
- tiny YIFY-style files where further compression will visibly degrade;
- files with known corruption, weird timestamps, or active Plex optimized versions;
- anything inside `$RECYCLE.BIN`, `System Volume Information`, or `Plex Versions` unless explicitly requested.

## Verification Checklist

- [ ] `ffmpeg.exe` and `ffprobe.exe` resolve and report versions.
- [ ] Input path is an imported copy under `D:\HermesTranscoderTest\Imports`.
- [ ] Output path is under `D:\HermesTranscoderTest\Outputs`.
- [ ] FFmpeg return code is zero.
- [ ] FFprobe can read output.
- [ ] Duration is approximately equal to source.
- [ ] Video codec is expected (`hevc`/x265 for output).
- [ ] Audio/subtitle streams are preserved or differences are documented.
- [ ] Size ratio is recorded.
- [ ] No original file was modified, deleted, or overwritten.

## Common Pitfalls

1. **Windows FFmpeg + WSL paths.** Passing `/mnt/d/foo.mkv` to Windows `ffmpeg.exe` can produce `Permission denied`. Translate to `D:\foo.mkv` or use the Python helper's path translation.

2. **Copying audio unnecessarily.** Re-encoding audio wastes time and can reduce quality. Copy audio unless space analysis proves audio is the major size component.

3. **Over-compressing already-small files.** If the source is already low bitrate, x265 may save little or produce artifacts. Some files are already dead; squeezing the corpse is not engineering.

4. **Batching before representative tests.** Run separate tests for animation, grainy film, clean 1080p web, old AVI/MPEG2, and long dark scenes.

5. **Forgetting subtitles/chapters.** Always use `-map 0 -map_metadata 0 -map_chapters 0` for archive-style transcodes.

6. **Trusting size only.** A 70% reduction can be good or a crime scene. Spot-check visually before scaling.

## Building Helper Programs

When building scripts for Xan's media folders:

- Put durable code under `/mnt/c/Users/santi/Documents/GitHub/transcoder` unless told otherwise.
- Put test data under `/mnt/d/HermesTranscoderTest`.
- Use manifests and JSON reports.
- Prefer dry-run modes for batch operations.
- Add explicit roots instead of guessing.
- Block writes outside the test workspace unless a command-line override and explicit user approval exist.
