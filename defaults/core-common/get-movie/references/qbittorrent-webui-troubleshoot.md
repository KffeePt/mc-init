# qBittorrent Web UI Troubleshooting

## Issue: Web UI Not Listening on Port 8080

### Symptom
- qBittorrent running (visible in tasklist)
- BT port listening (e.g., 26228)
- `netstat` shows NO listening socket on 8080
- curl returns connection refused

### Root Cause: Password Format

qBittorrent **will not start Web UI** if password is stored as plaintext in `qBittorrent.ini`. The password must be a PBKDF2 hash.

**Incorrect:**
```ini
WebUI\Password=<redacted; read from local qBittorrent config only when needed>
```

**Correct:**
```ini
WebUI\Password_PBKDF2=@ByteArray(2190ccb0aad0309b73221ee1d9e0c09057a770cd09e59c270ad14bc5890cc3e124e22ba44b4d8bb79ebd54dca0d7a29d000186a0)
```

### Fix Procedure

#### 1. Generate PBKDF2 Hash
```python
import hashlib, os
password = os.getenv("QBITTORRENT_PASSWORD")  # do not hardcode secrets
salt = os.urandom(16)
iterations = 100000
hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations, dklen=32)
hash_formatted = f"@ByteArray({salt.hex()}{hash_obj.hex()}{iterations:08x})"
print(f"WebUI\\Password_PBKDF2={hash_formatted}")
```

#### 2. Update qBittorrent.ini
Location: `C:\Users\santi\AppData\Roaming\qBittorrent\qBittorrent.ini`
Replace plaintext with PBKDF2 hash.

#### 3. FULL RESTART
1. Close qBittorrent (system tray → Exit)
2. Wait 2 seconds
3. Restart qBittorrent
4. Wait 5-10 seconds for Web UI initialization

#### 4. Verify
```bash
netstat.exe -ano | grep "8080" | grep "LISTENING"
curl -u $QBITTORRENT_USERNAME:$QBITTORRENT_PASSWORD "http://localhost:8080/api/v2/torrents/info"
```

## Config Validation Checklist
- [ ] `WebUI\Enabled=true`
- [ ] `WebUI\Port=8080`
- [ ] `WebUI\Username=<local username, do not commit secrets>`
- [ ] `WebUI\Password_PBKDF2=@ByteArray(...)` ← NOT plaintext
- [ ] `WebUI\LocalHostAuth=false`
- [ ] `Downloads\SavePath=D:\\Movies\\`

## API Authentication Flow
```bash
# Login (gets SID cookie)
curl -s "http://localhost:8080/api/v2/auth/login" \
  --data-urlencode "username=$QBITTORRENT_USERNAME" \
  --data-urlencode "password=$QBITTORRENT_PASSWORD" \
  -c /tmp/qb_cookies.txt

# Use SID cookie
curl -b /tmp/qb_cookies.txt \
  "http://localhost:8080/api/v2/torrents/add" \
  --data-urlencode "urls=$MAGNET_LINK" \
  --data-urlencode "savepath=D:\\Movies\\"
```