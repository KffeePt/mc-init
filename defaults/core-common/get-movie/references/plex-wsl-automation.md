# Plex WSL Automation Pattern

## Context

WSL2 cannot access Windows localhost directly due to network isolation. Need to determine Windows host IP and use it for Plex API calls from WSL.

## Setup Pattern

### 1. Extract Plex Token

Open Plex Web UI in browser → F12 → Network tab → Make any request → Look for `X-Plex-Token` header in request/response headers.

Token is stable — extract once, reuse indefinitely.

### 2. Store Token

```bash
echo "YOUR_PLEX_TOKEN" > /home/xantastique/.hermes/plex_token.txt
chmod 600 /home/xantastique/.hermes/plex_token.txt
```

### 3. Determine Windows Host IP

```bash
# From WSL, the Windows host IP is typically:
ip route show | grep default
# Output: default via 192.168.128.1 dev eth0
```

For standard WSL2, this is usually `192.168.128.1`.

### 4. Helper Script Pattern

Create `/home/xantastique/.hermes/scripts/plex_scan.py`:

```python
#!/usr/bin/env python3
import sys
import os
import requests

PLEX_HOST = "192.168.128.1"
PLEX_PORT = 32400
TOKEN_FILE = "/home/xantastique/.hermes/plex_token.txt"

def get_token():
    with open(TOKEN_FILE, 'r') as f:
        return f.read().strip()

def get_url(path):
    token = get_token()
    return f"http://{PLEX_HOST}:{PLEX_PORT}{path}?X-Plex-Token={token}"

def list_sections():
    url = get_url("/library/sections")
    resp = requests.get(url)
    print(resp.text)

def refresh_section(section_id):
    url = get_url(f"/library/sections/{section_id}/refresh")
    resp = requests.put(url)
    print(f"Refresh triggered for section {section_id}: {resp.status_code}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    if cmd == "list":
        list_sections()
    elif cmd == "refresh" and len(sys.argv) > 2:
        refresh_section(sys.argv[2])
    else:
        print("Usage: plex_scan.py [list|refresh <section_id>]")
```

Make executable:
```bash
chmod +x /home/xantastique/.hermes/scripts/plex_scan.py
```

## Usage

```bash
# List all library sections
python3 /home/xantastique/.hermes/scripts/plex_scan.py list

# Refresh Movies section
python3 /home/xantastique/.hermes/scripts/plex_scan.py refresh 1
```

## Verified Section IDs

From current setup:
- **1**: Movies → `D:\Movies`
- **2**: TV Shows → `F:\Shows`
- **3**: Music → `F:\Music`
- **4**: Edits → `F:\Edits`

## Verification

Test connection:
```bash
curl -s "http://192.168.128.1:32400/library/sections?X-Plex-Token=YOUR_TOKEN"
```

Expected output: XML MediaContainer with Directory elements.

## Notes

- Tokens are durable; they do not rotate automatically
- Windows IP can change between WSL restarts; check `ip route` if API calls fail
- Plex Web UI is at `http://localhost:32400/web` on Windows, but use host IP from WSL
- Refresh is asynchronous; items appear after Plex processes them