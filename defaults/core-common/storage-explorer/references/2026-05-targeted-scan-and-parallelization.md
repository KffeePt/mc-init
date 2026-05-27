# 2026-05-27 Targeted Scan Defaults & Parallelization

Session reference for the `storage-explorer` skill. Captures the lessons from the MAMBA→BIGGIE hash verification attempts and the shift from brute-force to targeted scanning.

## Context

Xan asked to hash-verify files copied from MAMBA (F:\Shows) to BIGGIE Archived (D:\Archived Shows). Multiple approaches were tried; most failed due to WSL I/O interop tax and single-threaded bottlenecking.

## Key Lesson: Targeted First, Brute Force Only On Command

The default posture changed from "scan everything and figure it out" to "discover the target first, then scope the scan."

### Before (bad)
- "Hash all 5,384 matched episodes" → 36 hours
- "Hash a random sample of 209" → still 2+ hours via WSL interop
- "Run a whole-drive duplicate scan" → disk sleep, killed

### After (good)
- "What changed?" → check CreationTime windows → 2,894 files copied in a specific window
- "Which of those are new copies?" → match against MAMBA source → narrow to 169 missing episodes
- "Sample 100 of those" → 100 files is tractable
- "Hash only those 100" → minutes, not hours

### Rule

**Whole-drive brute-force scans require explicit user approval.** Default to:
1. Ask what changed (time window, specific folders, specific shows)
2. Match the pass to the question (show-level, episode-level, hash sample)
3. Escalate only when findings demand it
4. If the user says "hash everything" or "scan the whole drive," comply but warn about expected duration

## Parallelization: 2–7 Workers

### Why
Single-threaded SHA-256 hashing on spinning disk from WSL: ~0.02 eps/sec. At that rate, 5,384 files = ~74 hours. Unacceptable.

### Worker Count Formula
- Detect CPU cores: `os.cpu_count()` or `$env:NUMBER_OF_PROCESSORS`
- Cap at 7 (spinning disk seek contention dominates beyond 7)
- Floor at 2 (single-threaded is never acceptable for hash/scan work)
- Recommended: `min(7, max(2, floor(cores * 0.75)))`

### Python Pattern
```python
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

workers = min(7, max(2, os.cpu_count() * 3 // 4))
with ProcessPoolExecutor(max_workers=workers) as ex:
    futures = {ex.submit(hash_file, p): p for p in files}
    for f in as_completed(futures):
        results[futures[f]] = f.result()
```

Use `ProcessPoolExecutor`, NOT `ThreadPoolExecutor` — the GIL serializes CPU-bound work.

### PowerShell Pattern
```powershell
$files | ForEach-Object -Parallel {
    (Get-FileHash -Path $_.FullName -Algorithm SHA256).Hash
} -ThrottleLimit 4
```

### Go Preference
For reusable cross-platform tools (scan, hash, compare), prefer Go:
- Goroutines + channels for clean worker pools
- Single binary — no Python venv, no PowerShell version issues
- Runs natively on both WSL and Windows without interop tax
- Example pattern:
```go
sem := make(chan struct{}, workers)
var wg sync.WaitGroup
for _, path := range files {
    wg.Add(1)
    sem <- struct{}{}
    go func(p string) {
        defer wg.Done()
        defer func() { <-sem }()
        results.Store(p, sha256File(p))
    }(path)
}
wg.Wait()
```

## WSL Launch Interop Tax

All Windows processes launched from WSL (whether `powershell.exe`, `cmd.exe`, or `python.exe`) pay a ~26 MB/s I/O tax when reading large files from `/mnt/d` or `/mnt/f`. This is the WSL 9p filesystem bridge, not a disk limitation.

### Mitigations
1. **Detach fully:** `cmd.exe /c start /B powershell.exe -File ...` reduces (but doesn't eliminate) the tax.
2. **Use Windows-native background scheduling:** Task Scheduler or a Windows-side cron equivalent for long jobs.
3. **Accept the tax for small jobs:** If the job is <100 files, 26 MB/s is tolerable.
4. **Go binaries run at native speed** — another reason to prefer Go for reusable tools.

### Never Do This
- Launch two concurrent disk-intensive processes from WSL on the same physical disk. They thrash each other into single-digit MB/s.
- Keep a stale hash process running while launching a new one. Kill stragglers first.

## Progress Reporting

Every parallel hash/scan job must write `progress.json` periodically:
```json
{"done": 40, "total": 100, "match": 40, "mismatch": 0, "error": 0, "elapsed": 1740.5, "rate": "0.023 eps/sec", "etaMinutes": 43.5}
```
