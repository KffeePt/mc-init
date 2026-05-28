# PowerShell-through-WSL Execution Pitfalls

Lessons from deploying `qbittorrent-flatten-refresh.ps1` on 2026-05-25.

## 1. Copy-Item, not Move-Item, for qBittorrent-seeded files

qBittorrent holds read handles on completed torrents during seeding. `Move-Item` requires exclusive access and will fail with "file in use." `Copy-Item` works because it only needs read access. After copying, try `Remove-Item` on the source — if it fails (seed lock), that's fine; the file stays in the original location until qBittorrent releases it.

Pattern:
```powershell
Copy-Item -LiteralPath $source -Destination $dest -Force
$copied++
try { Remove-Item -LiteralPath $source -Force; $deleted++ } catch {}
```

During active download (pre-completion), files have exclusive write locks and `Copy-Item` will also hang. This only matters during testing — the production qBittorrent hook fires AFTER completion.

## 2. Don't use robocopy from WSL→PowerShell chain

`robocopy` argument parsing through WSL bash → PowerShell → robocopy.exe breaks on paths containing spaces. The intermediate shell layers mangle quoting. Stick to PowerShell-native cmdlets: `Copy-Item -LiteralPath`, `Remove-Item -LiteralPath`, `Get-ChildItem`.

## 3. PowerShell heredoc backslash doubling

When writing PowerShell scripts via WSL (write_file tool), backslashes in here-strings can get doubled. A regex like `'^D:\\Shows'` may become `'^D:\\\\Shows'` in the file, which won't match. Always parse-verify the script after writing:

```powershell
$errors = $null
[System.Management.Automation.Language.Parser]::ParseFile("path.ps1", [ref]$null, [ref]$errors)
if ($errors.Count -eq 0) { "OK" } else { $errors }
```

## 4. PowerShell `-replace` from WSL bash is a quoting nightmare

Avoid doing `powershell.exe -Command '... -replace ...'` from WSL bash. The nested quoting between bash, PowerShell, and regex quickly becomes unmaintainable. Use the `patch` tool on the .ps1 file directly instead.

## 5. PowerShell `$` variable expansion in WSL

When running PowerShell one-liners from WSL bash, wrap in single quotes or escape `$` — otherwise bash tries to expand `$var` before PowerShell sees it. Use:

```bash
powershell.exe -NoProfile -Command '$r = Get-Process; Write-Host $r.Count'
```

NOT:

```bash
powershell.exe -NoProfile -Command "$r = Get-Process; Write-Host $r.Count"
```

## 6. Start qBittorrent cleanly from WSL

```bash
powershell.exe -NoProfile -Command 'Start-Process -FilePath "C:\Program Files\qBittorrent\qBittorrent.exe"'
```

Then wait ~8 seconds for the Web UI to become available before making API calls.

## 7. Backtick escaping breaks from WSL bash → PowerShell

When running `powershell.exe -Command "..."` and the PowerShell script contains backtick-escaped newlines (``` ``n ```), backtick-escaped variables (``` `$ ```), or backtick line-continuations, **bash interprets the backticks** before PowerShell sees them. The result is a mangled script that PowerShell can't parse.

Example that breaks from WSL bash:

```bash
powershell.exe -NoProfile -Command "
  Write-Host 'hello`nworld'
  `$var = 42
"
```

The backticks get consumed or corrupted by bash, producing syntax errors like `unexpected EOF while looking for matching ``'`.

**Fix: write the script to a temp file, invoke with `-File`.** This avoids all bash→PowerShell escaping problems:

```bash
write_file /tmp/my_script.ps1 '
Write-Host "hello`nworld"
$var = 42
Write-Host $var
'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File /tmp/my_script.ps1
```

This was discovered 2026-05-25 when querying qBittorrent status — three separate `-Command` attempts with `$you | ForEach-Object { ... }` failed with bash quoting errors. The temp-file pattern worked on the first try.
