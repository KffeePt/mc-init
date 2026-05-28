# Plex Token Extraction — Auto-Scanner Setup

## Problem

Plex API requires authentication via `X-Plex-Token` header. Token is stored in `Preferences.xml` but location varies by platform and Windows configuration.

## Standard Plex Config Locations

**Windows:**
- `C:\Users\<USER>\AppData\Local\Plex Media Server\Preferences.xml`
- `C:\Users\<USER>\AppData\Roaming\Plex Media Server\Preferences.xml`
- `C:\ProgramData\Plex Media Server\Preferences.xml`

**Linux:**
- `~/.config/Plex Media Server/Preferences.xml`
- `/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Preferences.xml`

**macOS:**
- `~/Library/Application Support/Plex Media Server/Preferences.xml`

## Finding the Token

### Method 1: Browser DevTools (Fastest)

1. Open `http://localhost:32400/web` in browser
2. Press `F12` to open DevTools
3. Go to **Network** tab
4. Refresh the page
5. Click any request to `plex.tv`
6. Look for **`X-Plex-Token`** in Request Headers
7. Copy that string (format: `X-Plex-Token: abc123xyz...`)

### Method 2: Plex Settings UI

1. Open `http://localhost:32400/web`
2. Click **Settings** ⚙️ (top right gear icon)
3. Go to **Network** → **Show Advanced**
4. Token will be displayed in settings panel

### Method 3: Config File (PowerShell)

If `Preferences.xml` exists:

```powershell
Get-Content "$env:LOCALAPPDATA\Plex Media Server\Preferences.xml" | Select-String "PlexOnlineToken"
```

Returns: `PlexOnlineToken="<TOKEN>"`

**Pitfall:** On Xan's system, `Preferences.xml` was not found in any standard location. May be in non-default path or Plex uses different config storage.

## Plex API Endpoints

**Base URL:** `http://localhost:32400`

**Library sections:**
```bash
curl -H "X-Plex-Token: <TOKEN>" "http://localhost:32400/library/sections"
```

Returns XML with section IDs (Movies, TV Shows, etc.).

**Scan library section:**
```bash
curl -X PUT \
  -H "X-Plex-Token: <TOKEN>" \
  "http://localhost:32400/library/sections/<SECTION_ID>/refresh"
```

**Scan specific item (movie/episode):**
```bash
curl -X PUT \
  -H "X-Plex-Token: <TOKEN>" \
  "http://localhost:32400/library/sections/<SECTION_ID>/refresh?path=<ITEM_ID>"
```

## Auto-Scanner Architecture

**Goal:** When qBittorrent download completes, trigger Plex library refresh for affected section.

**Components:**
1. **Cron job** — runs every 5 minutes
2. **Watcher script** — queries qBittorrent API for completed downloads
3. **Path mapping** — maps qBittorrent save paths to Plex library sections
4. **Trigger scan** — sends PUT request to Plex API

**Path mappings (Xan's setup):**
- `D:\Movies\` → Movies section (SECTION_ID needed)
- `F:\Shows\` → TV Shows section (SECTION_ID needed)
- `F:\Music\` → Music section (SECTION_ID needed)

**Cron entry:**
```cron
*/5 * * * * /usr/bin/python3 /home/xantastique/.hermes/skills/media/plex_scanner.py
```

**Script pseudocode:**
```python
import requests
import time

# Config
PLEX_TOKEN = "paste_here"
QB_URL = "http://localhost:8080/api/v2"
PLEX_URL = "http://localhost:32400"

# Map save paths to Plex section IDs
PATH_TO_SECTION = {
    "D:\\Movies\\": 1,      # Get actual IDs from /library/sections
    "F:\\Shows\\": 2,
    "F:\\Music\\": 3,
}

# State tracking (completed torrents)
STATE_FILE = "/tmp/plex_scanner_state.json"

def get_completed_torrents():
    """Query qBittorrent for completed torrents."""
    resp = requests.get(f"{QB_URL}/torrents/info", params={"filter": "completed"})
    return resp.json()

def trigger_plex_scan(save_path):
    """Trigger Plex refresh for the library section."""
    section_id = PATH_TO_SECTION.get(save_path)
    if not section_id:
        return False
    
    requests.put(
        f"{PLEX_URL}/library/sections/{section_id}/refresh",
        headers={"X-Plex-Token": PLEX_TOKEN}
    )
    return True

def main():
    # Load previous state
    # Get current completed torrents
    # Detect new completions
    # Trigger scans for new completions
    # Update state

if __name__ == "__main__":
    main()
```

## Troubleshooting

**Issue:** Plex returns 401 Unauthorized
- **Cause:** Token missing, expired, or incorrect
- **Fix:** Extract fresh token via DevTools

**Issue:** Preferences.xml not found
- **Cause:** Plex config in non-standard location
- **Fix:** Use DevTools method instead

**Issue:** Scan not triggering
- **Cause:** Wrong SECTION_ID or permissions
- **Fix:** Query `/library/sections` to get correct IDs

## Next Steps for Xan

1. Extract Plex token via DevTools
2. Get section IDs: `curl -H "X-Plex-Token: <TOKEN>" "http://localhost:32400/library/sections"`
3. Provide token and section IDs to agent
4. Agent creates `plex_scanner.py` script
5. Agent adds cron job
6. Test: Download movie → verify auto-scan triggers