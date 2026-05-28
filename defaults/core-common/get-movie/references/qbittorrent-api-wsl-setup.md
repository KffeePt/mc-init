# qBittorrent API Setup in WSL (Windows)

## Environment

- **OS:** Windows with WSL
- **qBittorrent path:** `C:\Program Files\qBittorrent\qBittorrent.exe`
- **Config file:** `C:\Users\santi\AppData\Roaming\qBittorrent\qBittorrent.ini`

## Critical Configuration Requirements

### 1. Password Hash Format (MANDATORY)

qBittorrent **REQUIRES** PBKDF2-HMAC-SHA256 hash, not plaintext.

**Wrong:**
```ini
WebUI\Password=<redacted; read from local qBittorrent config only when needed>
```

**Correct:**
```ini
WebUI\Password_PBKDF2=@ByteArray(<salt_hex><hash_hex><iterations_hex>)
```

**Python script to generate hash:**
```python
import hashlib
import os
import binascii

password = "your_password"
salt = os.urandom(16)
iterations = 100000

hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations, dklen=32)
hash_formatted = f"@ByteArray({salt.hex()}{hash_obj.hex()}{iterations:08x})"

print(f"WebUI\\Password_PBKDF2={hash_formatted}")
```

**Example output:**
```
WebUI\Password_PBKDF2=@ByteArray(2190ccb0aad0309b73221ee1d9e0c09057a770cd09e59c270ad14bc5890cc3e124e22ba44b4d8bb79ebd54dca0d7a29d000186a0)
```

### 2. Full Config Example

```ini
[Preferences]
WebUI\Enabled=true
WebUI\Port=8080
WebUI\LocalHostAuth=false
WebUI\Username=<local username, do not commit secrets>
WebUI\Password_PBKDF2=@ByteArray(2190ccb0aad0309b73221ee1d9e0c09057a770cd09e59c270ad14bc5890cc3e124e22ba44b4d8bb79ebd54dca0d7a29d000186a0)
WebUI\CSRFProtection=true
Downloads\SavePath=D:\\Movies\\
```

## WSL Networking Issue

**Problem:** Windows services on `localhost:8080` are NOT reachable from WSL `curl`. Even `curl.exe` (Windows curl from WSL) fails on auth due to CSRF protection blocking cross-origin requests.

**Symptom:**
```bash
# From WSL — connection refused
curl http://localhost:8080/api/v2/auth/login
# curl: (7) Failed to connect to localhost port 8080

# From WSL via Windows host IP — connects but auth fails
curl http://192.168.128.1:8080/api/v2/auth/login -d "username=$QBITTORRENT_USERNAME&password=$QBITTORRENT_PASSWORD"
# Returns: Unauthorized (401) — CSRF protection blocks it

# curl.exe from WSL — same CSRF issue
curl.exe -s -d "username=$QBITTORRENT_USERNAME&password=$QBITTORRENT_PASSWORD" http://localhost:8080/api/v2/auth/login
# Returns: Unauthorized (401)
```

**Root Cause:** qBittorrent's `CSRFProtection=true` rejects requests from non-localhost origins. WSL's `192.168.128.1` is treated as cross-origin. Even `curl.exe` from WSL inherits the WSL origin context.

**Solution: Use PowerShell as the API bridge.** PowerShell runs natively on Windows, so `Invoke-WebRequest` to `localhost:8080` is treated as same-origin and CSRF passes.

### PowerShell Bridge Pattern (RECOMMENDED)

```bash
powershell.exe -Command "
  # Login
  \$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
  \$r = Invoke-WebRequest -Uri 'http://localhost:8080/api/v2/auth/login' \
    -Method POST -Body 'username=$QBITTORRENT_USERNAME&password=$QBITTORRENT_PASSWORD' \
    -UseBasicParsing -SessionVariable session

  # Add torrent
  \$body = @{urls='magnet:?xt=urn:btih:HASH'; savepath='D:\\Movies\\'}
  \$r2 = Invoke-WebRequest -Uri 'http://localhost:8080/api/v2/torrents/add' \
    -Method POST -Body \$body -WebSession \$session -UseBasicParsing
  Write-Output \$r2.Content
"
```

**Why this works:** PowerShell executes on the Windows host natively. `localhost:8080` is genuinely local, so CSRF passes. The `-SessionVariable session` captures the SID cookie automatically.

**Important:** In bash, escape `$` as `\$` inside the PowerShell command string.

### Fallback: curl.exe from WSL (limited)

`curl.exe` can reach the service but auth fails with CSRF. Only works if you disable CSRF in qBittorrent config (`WebUI\CSRFProtection=false`) — not recommended.

## API Usage

### Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v2/auth/login` | POST | Get session cookie |
| `/api/v2/torrents/info` | GET | List all torrents |
| `/api/v2/torrents/add` | POST | Add torrent (magnet or file) |
| `/api/v2/torrents/setLocation` | POST | Change download path |

### Add Torrent — Full PowerShell Flow

```bash
powershell.exe -Command "
  \$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
  # Login (204 = success)
  \$r = Invoke-WebRequest -Uri 'http://localhost:8080/api/v2/auth/login' \
    -Method POST -Body 'username=$QBITTORRENT_USERNAME&password=$QBITTORRENT_PASSWORD' \
    -UseBasicParsing -SessionVariable session

  # Add torrent with save path
  \$body = @{urls='magnet:?xt=urn:btih:HASH&dn=Movie.Name&tr=...'; savepath='D:\\Movies\\'}
  \$r2 = Invoke-WebRequest -Uri 'http://localhost:8080/api/v2/torrents/add' \
    -Method POST -Body \$body -WebSession \$session -UseBasicParsing
  Write-Output \$r2.Content
"
```

Response:
```json
{
  "added_torrent_ids": ["a13c2b0af34c3e2f1ebca45858b12642cbdfe249"],
  "failure_count": 0,
  "pending_count": 0,
  "success_count": 1
}
```

### Verify Torrent Added

```bash
powershell.exe -Command "
  \$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
  \$r = Invoke-WebRequest -Uri 'http://localhost:8080/api/v2/auth/login' \
    -Method POST -Body 'username=$QBITTORRENT_USERNAME&password=$QBITTORRENT_PASSWORD' \
    -UseBasicParsing -SessionVariable session
  \$r2 = Invoke-WebRequest -Uri 'http://localhost:8080/api/v2/torrents/info' \
    -WebSession \$session -UseBasicParsing
  \$r2.Content | ConvertFrom-Json | ForEach-Object {
    Write-Output \"\$(\$_.name) | \$(\$_.state) | \$([math]::Round(\$_.progress*100,1))%\"
  }
"
```

## Verification

After configuration changes:

1. **Restart qBittorrent completely** (system tray → Exit → restart)
2. **Check port listening:**
   ```bash
   netstat.exe -ano | grep "8080" | grep "LISTENING"
   ```
3. **Test authentication:**
   ```bash
   curl.exe -u $env:QBITTORRENT_USERNAME:$env:QBITTORRENT_PASSWORD http://localhost:8080/api/v2/torrents/info
   # Should return JSON array (may be empty if no torrents)
   ```

## Startup Configuration

### Windows Startup Folder

**Path:** `C:\Users\santi\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\`

**Batch file (`start_qbittorrent.bat`):**
```batch
@echo off
REM qBittorrent Startup Script
start "" "C:\Program Files\qBittorrent\qBittorrent.exe"
timeout /t 10 /nobreak > nul
```

**Notes:**
- Use actual Windows username (`santi`), not WSL username (`xantastique`)
- Batch file runs on Windows login
- qBittorrent starts minimized in background

## Differences from uTorrent

| Feature | uTorrent | qBittorrent |
|---------|----------|-------------|
| **Web UI enablement** | ❌ Impossible via config (keys stripped) | ✅ INI config works |
| **Password format** | Plaintext | PBKDF2 hash required |
| **Authentication** | CSRF token + Basic Auth | Session cookie (SID) |
| **API format** | Token in URL, array response | Standard REST, JSON objects |
| **WSL networking** | ✅ Works via curl | ⚠️ Requires curl.exe |

## Common Pitfalls

1. **Wrong password format** → qBittorrent won't start Web UI, no error message
2. **Forgot to restart** → Config changes don't take effect
3. **Used WSL curl** → Connection refused (exit code 7)
4. **Used Windows host IP from WSL** → Connects but CSRF blocks auth (401 Unauthorized)
5. **Used curl.exe from WSL** → Same CSRF issue as #4
6. **PowerShell is the only working WSL bridge** → `powershell.exe -Command "Invoke-WebRequest ..."`
7. **Wrong username path** → Windows path uses `santi`, WSL uses `xantastique`
8. **Session cookie expires** → Re-authenticate if 401 errors
9. **Bash $ escaping** → Inside `powershell.exe -Command "..."`, escape `$` as `\$` in bash

## Debugging

```bash
# Check if qBittorrent is running
powershell.exe -Command "Get-Process -Name 'qbittorrent' -ErrorAction SilentlyContinue | Select-Object Id,ProcessName"

# Check which process owns port 8080
netstat.exe -ano | grep "8080" | grep "LISTENING"

# Test API from PowerShell (WORKS — same-origin, CSRF passes)
powershell.exe -Command "Invoke-WebRequest -Uri 'http://localhost:8080/api/v2/auth/login' -Method POST -Body 'username=$QBITTORRENT_USERNAME&password=$QBITTORRENT_PASSWORD' -UseBasicParsing"

# Test from WSL via host IP (FAILS — CSRF blocks cross-origin)
curl -s "http://192.168.128.1:8080/api/v2/auth/login" -d "username=$QBITTORRENT_USERNAME&password=$QBITTORRENT_PASSWORD"
# Returns: Unauthorized

# Read qBittorrent config
cat "/mnt/c/Users/santi/AppData/Roaming/qBittorrent/qBittorrent.ini" | grep -iE "WebUI|CSRF|Port"
```