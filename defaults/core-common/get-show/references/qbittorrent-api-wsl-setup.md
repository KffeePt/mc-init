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

**Problem:** Windows services on `localhost:8080` may not be reachable from WSL's `curl` command.

**Symptom:**
```bash
curl http://localhost:8080/api/v2/auth/login
# Returns: curl: (7) Failed to connect to localhost port 8080 after X ms: Connection refused
```

**Solution:** Use Windows `curl.exe` instead of WSL `curl`.

**Python subprocess command:**
```python
cmd = [
    "curl.exe",  # NOT "curl"
    "-s", "--max-time", "5",
    "-c", cookie_file,
    "--data-urlencode", f"username={QB_USER}",
    "--data-urlencode", f"password={QB_PASS}",
    url
]
subprocess.run(cmd, capture_output=True, timeout=10)
```

**Why:** Windows services listen on Windows loopback, WSL has separate networking namespace. Windows curl.exe can reach Windows services; WSL curl cannot.

## API Usage

### Authentication Flow

```bash
# 1. Login (saves SID cookie)
curl.exe -s -c /tmp/qb_cookies.txt \
  --data-urlencode "username=$QBITTORRENT_USERNAME" \
  --data-urlencode "password=$QBITTORRENT_PASSWORD" \
  http://localhost:8080/api/v2/auth/login

# 2. Use session cookie for API calls
curl.exe -s -b /tmp/qb_cookies.txt \
  http://localhost:8080/api/v2/torrents/info
```

### Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v2/auth/login` | POST | Get session cookie |
| `/api/v2/torrents/info` | GET | List all torrents |
| `/api/v2/torrents/add` | POST | Add torrent (magnet or file) |
| `/api/v2/torrents/setLocation` | POST | Change download path |

### Add Torrent with Destination

```bash
curl.exe -s -b /tmp/qb_cookies.txt \
  "http://localhost:8080/api/v2/torrents/add" \
  --data-urlencode "urls=magnet:?xt=urn:btih:HASH" \
  --data-urlencode "savepath=D:\\Movies\\"
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
3. **Used WSL curl** → Connection refused, exit code 7
4. **Wrong username path** → Windows path uses `santi`, WSL uses `xantastique`
5. **Session cookie expires** → Re-authenticate if 401 errors

## Debugging

```bash
# Check if qBittorrent is running
tasklist.exe | grep -i "qbittorrent"

# Check which process owns port 8080
netstat.exe -ano | grep "8080" | grep "LISTENING"

# Test API manually
curl.exe -s -u $QBITTORRENT_USERNAME:$QBITTORRENT_PASSWORD http://localhost:8080/api/v2/torrents/info | jq

# Test from WSL (will fail - expected behavior)
curl -s -u $QBITTORRENT_USERNAME:$QBITTORRENT_PASSWORD http://localhost:8080/api/v2/torrents/info
```