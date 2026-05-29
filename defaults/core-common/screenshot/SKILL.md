---
name: screenshot
description: Capture Windows screenshots using the shared Hermes screenshot helper.
version: 1.0.0
author: Wilson / Hermes Agent
license: MIT
platforms: [windows, wsl]
metadata:
  hermes:
    tags: [screenshot, helper, windows, capture, artifact]
    related_skills: [get-artifact]
---

# Screenshot Helper

## When to Use

Use when Xan asks for a screenshot, visual proof of the Windows desktop, UI state capture, or a screen artifact for troubleshooting.

## Helper Location

Canonical helper path on Windows:

```text
C:\Users\santi\Documents\Hermes\helpers\screenshot\take-screenshot.ps1
```

WSL path on Xan's controller machine:

```text
/mnt/c/Users/santi/Documents/Hermes/helpers/screenshot/take-screenshot.ps1
```

All reusable copied scripts are called **helpers** and live under `Documents\Hermes\helpers\<skill-name>\` even when a skill also bundles its own scripts.

## Usage

From Windows PowerShell:

```powershell
& "$env:USERPROFILE\Documents\Hermes\helpers\screenshot\take-screenshot.ps1"
```

Optional explicit output:

```powershell
& "$env:USERPROFILE\Documents\Hermes\helpers\screenshot\take-screenshot.ps1" -OutputPath "$env:USERPROFILE\Documents\Hermes\Artifacts\Screenshots\screen.png"
```

From WSL targeting the Windows host:

```bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\\Users\\santi\\Documents\\Hermes\\helpers\\screenshot\\take-screenshot.ps1"
```

## Output

The helper prints compact JSON:

```json
{"ok":true,"path":"...","bytes":12345,"width":1920,"height":1080}
```

## Safety

Screenshots may contain credentials, private chats, tokens, browser tabs, or personal files. Capture when requested, but inspect/redact before external delivery if the scope is not explicitly local/private.

## Verification Checklist

- [ ] Helper exists under `Documents\Hermes\helpers\screenshot\`.
- [ ] Command returns `ok: true` JSON.
- [ ] Output PNG exists and is nonzero bytes.
- [ ] Sensitive visible content considered before sending externally.
