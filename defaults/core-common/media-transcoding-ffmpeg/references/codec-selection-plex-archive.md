# Codec Selection for Plex Archive Compression

Use this reference when Xan asks which codec/settings to use for reducing Plex/media-library storage pressure.

## Recommended default

For Xan's Plex/archive workflow, the practical default is:

```text
HEVC / H.265 / x265
10-bit output
CRF 21-22 for quality archive work, CRF 23 for faster tests
preset slow for serious runs, medium for smoke tests
MKV container
audio/subtitles copied unless analysis proves they dominate size
```

Core FFmpeg options:

```bash
-map 0 -map_metadata 0 -map_chapters 0 \
-c:v libx265 -preset slow -crf 22 -pix_fmt yuv420p10le \
-c:a copy -c:s copy
```

Fast test variant:

```bash
-c:v libx265 -preset medium -crf 23 -pix_fmt yuv420p10le
```

## Codec decision matrix

### HEVC / H.265 / x265

Best operational balance for Xan's current library: strong compression, tolerable compatibility, and not absurdly slow compared with AV1.

Use for:

- old MPEG2/DVD-era material;
- AVI/Xvid-era TV;
- bloated H.264 movies/shows;
- 1080p web/bluray encodes above expected size;
- controlled archive compression where Plex compatibility still matters.

Avoid or skip when:

- source is already efficient HEVC/x265 unless unusually bloated;
- source is tiny/low-bitrate and visible damage is likely;
- direct-play compatibility for very old clients is more important than storage.

### AV1

Technically better compression, weaker operational fit for this server unless hardware/client support is known.

Pros:

- often smaller than x265 at similar subjective quality;
- strong for clean animation and digital sources;
- future-facing.

Cons:

- CPU encoding is much slower;
- Plex/client compatibility can force transcoding;
- not the first default for a live mixed Plex library.

Use only after x265 baselines, for selected classes such as animation or rarely watched content.

### H.264 / x264

Compatibility fallback, not the storage-saving default.

Use when old-device direct play is the primary requirement. Otherwise it is usually the wrong answer for this storage-pressure problem.

### VP9

Not recommended for this Plex archive workflow. Use HEVC or AV1 instead.

## Expected savings reality check

Old inefficient MPEG2 sources can shrink dramatically under x265. One observed short 480p MPEG2 sample went from roughly 651 MB to 142 MB with x265 CRF 23 medium 10-bit while copying AC3 audio streams: about 78% reduction.

Do not generalize that number across the library:

- MPEG2/Xvid/AVI -> HEVC: often large savings.
- H.264 -> HEVC: more commonly 20-50% depending on source and quality target.
- HEVC -> HEVC: usually poor return and added generation loss unless the source is obviously bloated/bad.

## Audio policy

Default to `-c:a copy`. Re-encode audio only after stream analysis shows audio is a major size component or compatibility requires it.

Reason: audio re-encoding can reduce quality, break surround layouts, trigger compatibility issues, and introduce sync/subtitle weirdness. Treat it as a separate decision, not a side effect of video compression.

## Operational warning

Do not run a whole-drive transcode based on one good sample. Use:

```text
probe -> classify -> representative tests -> compare -> batch only safe classes
```

Never:

```text
throw entire drive into ffmpeg and pray
```

Prayer is still not a backup strategy.
