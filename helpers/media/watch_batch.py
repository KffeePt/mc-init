#!/usr/bin/env python3
"""
Watch a batch of torrents in qBittorrent until all complete.
Scan, then refresh Plex, then exit.

Usage: watch_batch.py <torrent_name_1> <torrent_name_2> ...

Runs in background, polls every 5 minutes.
"""

import subprocess
import json
import sys
import time
import os
import argparse
from datetime import datetime
import hashlib

sys.path.insert(0, '/home/xantastique/.hermes/skills/media')
from lib.qbittorrent import QBittorrentClient

# Paths
MOVIES_DIR = "/mnt/d/Movies/"
SHOWS_DIR = "/mnt/d/Shows/"
PLEX_SECTION = "Movies"
POLL_INTERVAL = 300  # 5 minutes
MAX_WAIT_HOURS = 24
WATCHER_LOGS = os.path.expanduser("~/.hermes/logs/watchers")
ACTIVE_BATCHES = os.path.expanduser("~/.hermes/logs/watchers/active_batches.json")

def setup_logging(batch_id):
    """Setup batch-specific logging"""
    os.makedirs(WATCHER_LOGS, exist_ok=True)
    log_file = os.path.join(WATCHER_LOGS, f"{batch_id}.log")
    return log_file

def log(msg, log_file=None):
    """Log to console and optionally to file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    print(msg, flush=True)

    if log_file:
        try:
            with open(log_file, 'a') as f:
                f.write(line)
        except:
            pass

def get_qbittorrent_status():
    """Get current torrent status from qBittorrent as structured data."""
    try:
        data = QBittorrentClient().get_torrents()
        if data.get('status') != 'ok':
            print(f"ERROR: qBittorrent status failed: {data.get('message')}")
            return {}

        torrents = {}
        for t in data.get('torrents', []):
            name = t.get('name')
            if not name:
                continue
            progress = str(t.get('progress', ''))
            is_complete = progress.startswith('100.0') or t.get('status') == '✅ Complete' or float(t.get('progress_pct', 0) or 0) >= 100.0
            t['is_complete'] = is_complete
            torrents[name] = t
        return torrents
    except Exception as e:
        print(f"ERROR: Failed to get qBittorrent status: {e}")
    return {}

def names_match(target, candidate):
    """Fuzzy match between torrent names"""
    # Normalize: lowercase, remove special chars
    def normalize(n):
        import re
        # Drop square-bracket release/quality tags like [1080p], [YTS.MX], [WEBRip].
        # Keep parenthesized years so Title (2024) still matches torrent names.
        n = re.sub(r'\[[^\]]+\]', ' ', n)
        n = re.sub(r'\b(480p|720p|1080p|2160p|4k|webrip|web[- ]?dl|bluray|brrip|hdtv|x264|x265|hevc|aac|ddp|dts|5\.1|10bit)\b', ' ', n, flags=re.I)
        return ''.join(c.lower() for c in n if c.isalnum() or c.isspace())

    norm_target = normalize(target)
    norm_candidate = normalize(candidate)

    # Check if all words from target appear in candidate (order-independent)
    target_words = set(norm_target.split())
    candidate_words = set(norm_candidate.split())

    # If most target words appear in candidate, it's a match
    if len(target_words) == 0:
        return False

    match_count = len(target_words.intersection(candidate_words))
    return match_count >= len(target_words) * 0.7  # 70% word match threshold

def scan_file(path):
    """Quick scan of a file/folder - returns True if safe"""
    # Extension check
    if path.lower().endswith(('.exe', '.bat', '.dll', '.ps1', '.scr', '.iso', '.msi')):
        return False

    # Check if it's a directory
    if os.path.isdir(path):
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file_path.lower().endswith(('.exe', '.bat', '.dll', '.ps1', '.scr', '.iso', '.msi')):
                        return False
        except:
            pass

    # Basic size check
    if os.path.isfile(path):
        size_mb = os.path.getsize(path) / (1024 * 1024)
        if size_mb < 50:
            return False

    return True

def refresh_plex(section):
    """Trigger Plex library refresh"""
    try:
        result = subprocess.run(
            ['python3', '/home/xantastique/.hermes/skills/media/get-movie/scripts/plex_refresh.py', '--section', section],
            capture_output=True, text=True, timeout=30
        )
        return "HTTP 200" in result.stdout
    except Exception as e:
        print(f"ERROR: Plex refresh failed: {e}")
        return False

def find_media_path(search_name, media_type):
    """Find the downloaded file/folder in the typed media directory."""
    base_dir = SHOWS_DIR if media_type in ('show', 'tv') else MOVIES_DIR
    try:
        if os.path.exists(base_dir):
            for entry in os.listdir(base_dir):
                # Try fuzzy match
                if names_match(search_name, entry):
                    return os.path.join(base_dir, entry)
    except:
        pass
    return None


def windows_path_to_wsl(path):
    """Convert D:\\Shows\\Name to /mnt/d/Shows/Name for local filesystem work."""
    if not path:
        return None
    p = str(path).strip().replace('\\', '/')
    if len(p) >= 2 and p[1] == ':':
        drive = p[0].lower()
        return f"/mnt/{drive}{p[2:]}"
    return p


def media_root_from_torrent(torrent, media_type):
    """Resolve qBittorrent save/content path to canonical media root.

    This is deliberately path-first, not fuzzy-title-first. Plex identifies
    media primarily from library root + folder/filename conventions; the
    watcher should do the same. Indexer names are polluted with release
    groups, tracker junk, and sometimes the wrong title. qBittorrent already
    knows the save path we chose: use it.
    """
    base_dir = SHOWS_DIR if media_type in ('show', 'tv') else MOVIES_DIR
    base_norm = os.path.normpath(base_dir)
    for key in ('save_path', 'content_path'):
        raw = torrent.get(key) if isinstance(torrent, dict) else None
        wsl = windows_path_to_wsl(raw)
        if not wsl:
            continue
        norm = os.path.normpath(wsl)
        if norm == base_norm or not norm.startswith(base_norm + os.sep):
            continue
        rel = os.path.relpath(norm, base_norm)
        first = rel.split(os.sep)[0]
        if first and first != '.':
            return os.path.join(base_norm, first)
    return None


def show_root_from_torrent(torrent):
    """Resolve qBittorrent save/content path to canonical /mnt/d/Shows/<Show> root."""
    return media_root_from_torrent(torrent, 'show')


def movie_root_from_torrent(torrent):
    """Resolve qBittorrent save/content path to canonical /mnt/d/Movies/<Movie> root."""
    return media_root_from_torrent(torrent, 'movie')


def media_identity_from_root(root, media_type):
    """Extract Plex-style identity from canonical folder/filename patterns.

    Movies: Title (Year) folder. Shows: Show (Year) + SxxExx filenames.
    This is not a remote IMDb lookup; it is the same practical metadata shape
    Plex expects, and avoids brittle release-name matching.
    """
    import re
    name = os.path.basename(os.path.normpath(root or ''))
    m = re.match(r'^(?P<title>.+?)\s*\((?P<year>\d{4})\)\s*$', name)
    ident = {'root': root, 'folder': name, 'title': name, 'year': None, 'episodes': []}
    if m:
        ident['title'] = m.group('title').strip()
        ident['year'] = m.group('year')
    if media_type in ('show', 'tv') and root and os.path.isdir(root):
        ep_re = re.compile(r'[Ss](\d{1,2})[ ._\-]*[Ee](\d{1,2})')
        episodes = set()
        for r, _, files in os.walk(root):
            for fn in files:
                em = ep_re.search(fn)
                if em:
                    episodes.add(f"S{int(em.group(1)):02d}E{int(em.group(2)):02d}")
        ident['episodes'] = sorted(episodes)
    return ident


def clean_download_name(name):
    """Strip tracker junk without destroying normal dotted release names."""
    import re
    cleaned = re.sub(r'(?i)(?:https?://\S+|www\.[a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)+\b)(?:\s*[-_.]\s*)?', '', name)
    cleaned = re.sub(r'(?i)\[(?:eztvx?\.to|tgx|torrentgalaxy|uindex\.org|rarbg|yts\.mx)\]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip(' ._-')
    return cleaned or name


def flatten_show_root(show_root, log_file=None):
    """Flatten episodes under canonical Season N (Year) folders. Collision-safe."""
    import re, shutil, hashlib
    if not show_root or os.path.normpath(show_root) == os.path.normpath(SHOWS_DIR):
        log(f"   ⚠️ Flatten skipped unsafe show root: {show_root}", log_file)
        return {'moved': 0, 'duplicates': 0, 'collisions': 0, 'errors': 1}
    if not os.path.isdir(show_root):
        log(f"   ⚠️ Flatten skipped missing show root: {show_root}", log_file)
        return {'moved': 0, 'duplicates': 0, 'collisions': 0, 'errors': 1}

    year = ''
    m_year = re.search(r'\((\d{4})\)\s*$', os.path.basename(show_root))
    if m_year:
        year = m_year.group(1)
    ep_re = re.compile(r'[Ss](\d{1,2})[ ._\-]*[Ee](\d{1,2})')
    season_re = re.compile(r'^(Season\s+\d+\s*\(\d{4}\)|S\d+)$', re.I)
    exts = {'.mkv', '.mp4', '.avi', '.m4v', '.wmv', '.srt', '.sub', '.ass', '.ssa', '.vtt', '.nfo'}

    def digest(path):
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                h.update(chunk)
        return h.hexdigest()

    result = {'moved': 0, 'duplicates': 0, 'collisions': 0, 'errors': 0}
    candidates = []
    for root, _, files in os.walk(show_root):
        for fn in files:
            src = os.path.join(root, fn)
            if os.path.splitext(fn)[1].lower() not in exts:
                continue
            rel = os.path.relpath(src, show_root)
            parts = rel.split(os.sep)
            if len(parts) >= 2 and season_re.match(parts[0]):
                continue
            m = ep_re.search(fn)
            if not m:
                continue
            season = int(m.group(1))
            season_name = f"Season {season} ({year})" if year else f"Season {season}"
            dst = os.path.join(show_root, season_name, clean_download_name(fn))
            candidates.append((src, dst))

    for src, dst in candidates:
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            final = dst
            if os.path.exists(final):
                if os.path.getsize(src) == os.path.getsize(final) and digest(src) == digest(final):
                    os.remove(src)
                    result['duplicates'] += 1
                    continue
                base, ext = os.path.splitext(dst)
                final = f"{base}__COLLISION_REVIEW_{datetime.now().strftime('%Y%m%d-%H%M%S')}_{digest(src)[:12]}{ext}"
                result['collisions'] += 1
            shutil.move(src, final)
            result['moved'] += 1
        except Exception as e:
            log(f"   ⚠️ Flatten move failed: {src} -> {dst} | {e}", log_file)
            result['errors'] += 1

    for root, dirs, files in os.walk(show_root, topdown=False):
        if os.path.normpath(root) == os.path.normpath(show_root):
            continue
        try:
            if not os.listdir(root):
                os.rmdir(root)
        except Exception:
            pass

    log(f"   📁 Flatten {os.path.basename(show_root)}: moved={result['moved']} duplicates={result['duplicates']} collisions={result['collisions']} errors={result['errors']}", log_file)
    return result


def wsl_path_to_windows(path):
    if not path:
        return None
    p = os.path.normpath(path)
    if p.startswith('/mnt/') and len(p) > 6:
        drive = p[5].upper()
        rest = p[6:].replace('/', '\\')
        return f"{drive}:\\{rest}"
    return path


def ps_single_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def run_windows_smart_flatten(media_type, roots, hashes, log_file=None):
    """Use the shared Windows smart organizer functions when available.

    That path preserves Xan's review-queue semantics for real collisions and
    refreshes the right Plex section. If unavailable, the caller can fall back
    to Python-only flattening.
    """
    script = r'C:\Users\santi\Documents\Hermes\Scripts\qbittorrent-batch-lib.ps1'
    ps_probe = subprocess.run(
        ['powershell.exe', '-NoProfile', '-Command', f"Test-Path -LiteralPath {ps_single_quote(script)}"],
        capture_output=True, text=True, timeout=30,
    )
    if 'True' not in ps_probe.stdout:
        log(f"   ⚠️ Windows smart flatten library not found: {script}", log_file)
        return False

    win_roots = [wsl_path_to_windows(r) for r in sorted(roots) if r]
    clean_hashes = [h for h in sorted(set(hashes)) if h]
    roots_expr = '@(' + ','.join(ps_single_quote(r) for r in win_roots) + ')'
    hashes_expr = '@(' + ','.join(ps_single_quote(h) for h in clean_hashes) + ')'
    flatten_func = 'Flatten-HermesShowRoot' if media_type in ('show', 'tv') else 'Flatten-HermesMovieRoot'
    refresh_func = 'Invoke-HermesPlexShowsRefresh' if media_type in ('show', 'tv') else 'Invoke-HermesPlexMoviesRefresh'
    ps = (
        f". {ps_single_quote(script)}; "
        f"$hashes={hashes_expr}; if ($hashes.Count -gt 0) {{ Remove-HermesQbTorrentsKeepFiles $hashes | Out-Null }}; "
        f"$roots={roots_expr}; $failed=0; foreach($r in $roots) {{ "
        f"Write-Output ('FLATTEN ' + $r); $res={flatten_func} $r; "
        f"if ([int]$res.failed -gt 0) {{ $failed += [int]$res.failed }}; "
        f"$res | ConvertTo-Json -Compress }}; "
        f"if ($failed -eq 0) {{ {refresh_func} | Out-Null }}; "
        f"exit ([Math]::Min($failed, 99))"
    )
    try:
        result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps],
                                capture_output=True, text=True, timeout=300)
        for line in (result.stdout or '').splitlines():
            log(f"   {line}", log_file)
        if result.stderr:
            for line in result.stderr.splitlines():
                log(f"   ⚠️ PS: {line}", log_file)
        return result.returncode == 0
    except Exception as e:
        log(f"   ⚠️ Windows smart flatten failed: {e}", log_file)
        return False

def register_batch(batch_id, torrent_names, pid, media_type):
    """Register active batch"""
    os.makedirs(os.path.dirname(ACTIVE_BATCHES), exist_ok=True)

    try:
        with open(ACTIVE_BATCHES, 'r') as f:
            active = json.load(f)
    except:
        active = {}

    active[batch_id] = {
        'torrents': torrent_names,
        'pid': pid,
        'started_at': datetime.now().isoformat(),
        'status': 'watching',
        'media_type': media_type
    }

    with open(ACTIVE_BATCHES, 'w') as f:
        json.dump(active, f, indent=2)

def unregister_batch(batch_id):
    """Remove completed batch"""
    try:
        with open(ACTIVE_BATCHES, 'r') as f:
            active = json.load(f)
    except:
        return

    if batch_id in active:
        del active[batch_id]

    with open(ACTIVE_BATCHES, 'w') as f:
        json.dump(active, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Watch a typed qBittorrent batch until complete")
    parser.add_argument('--type', choices=['movie', 'show', 'tv', 'music'], default='movie',
                        help='Explicit media type; selects scan root and Plex section')
    parser.add_argument('torrent_names', nargs='+')
    args = parser.parse_args()

    media_type = args.type
    plex_section = 'Shows' if media_type in ('show', 'tv') else 'Movies'

    # Generate batch ID from torrent names
    batch_names = args.torrent_names
    batch_hash = hashlib.md5(' '.join(sorted(batch_names)).encode()).hexdigest()[:8]
    batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{batch_hash}"

    # Setup logging
    log_file = setup_logging(batch_id)

    log(f"🎬 Watching {media_type} batch {batch_id} of {len(batch_names)} torrent(s):", log_file)
    for name in batch_names:
        log(f"   - {name}", log_file)

    # Register batch
    register_batch(batch_id, batch_names, os.getpid(), media_type)

    start_time = datetime.now()
    completed_count = 0

    while True:
        # Check timeout
        elapsed = (datetime.now() - start_time).total_seconds()
        if elapsed > MAX_WAIT_HOURS * 3600:
            log(f"⏰ Timeout after {MAX_WAIT_HOURS} hours - giving up", log_file)
            unregister_batch(batch_id)
            sys.exit(1)

        # Get current status
        status = get_qbittorrent_status()

        if not status:
            log(f"⚠️ Could not get qBittorrent status, retrying...", log_file)
            time.sleep(60)
            continue

        # Check completion status
        batch_status = []
        all_complete = True

        for name in batch_names:
            # Find matching torrent in status (fuzzy match)
            found = False
            is_complete = False

            torrent_info = None
            for status_name, status_info in status.items():
                if names_match(name, status_name):
                    found = True
                    torrent_info = status_info
                    is_complete = bool(status_info.get('is_complete')) if isinstance(status_info, dict) else bool(status_info)
                    break

            if found:
                batch_status.append((name, is_complete, torrent_info))
                if not is_complete:
                    all_complete = False
            else:
                # Torrent not found - might be removed or not added yet
                log(f"⚠️ Torrent not found: {name}", log_file)
                batch_status.append((name, False, None))
                all_complete = False

        # Report status
        complete = sum(1 for _, c, _ in batch_status if c)
        if complete > completed_count:
            completed_count = complete
            log(f"📥 Progress: {complete}/{len(batch_names)} complete", log_file)

        if all_complete:
            log(f"✅ All {len(batch_names)} torrents complete!", log_file)
            break

        # Wait before next poll
        log(f"⏳ Waiting {POLL_INTERVAL//60} minutes...", log_file)
        time.sleep(POLL_INTERVAL)

    # All complete - scan and refresh
    log(f"🔬 Scanning downloaded files...", log_file)

    all_safe = True
    roots_to_flatten = set()
    completed_hashes = set()
    for name, _, torrent_info in batch_status:
        root = None
        if torrent_info:
            root = media_root_from_torrent(torrent_info, media_type)
            if root:
                roots_to_flatten.add(root)
                ident = media_identity_from_root(root, media_type)
                ep_note = f" episodes={','.join(ident['episodes'][:5])}" if ident.get('episodes') else ''
                log(f"   🔎 Path identity: {ident['title']} ({ident.get('year') or 'unknown year'}){ep_note}", log_file)
            if torrent_info.get('info_hash'):
                completed_hashes.add(torrent_info.get('info_hash'))
        path = root or find_media_path(name, media_type)
        if path:
            if scan_file(path):
                log(f"   ✅ {os.path.basename(path)} - SAFE", log_file)
            else:
                log(f"   ⚠️ {os.path.basename(path)} - SCAN FAILED", log_file)
                all_safe = False
        else:
            log(f"   ⚠️ {name} - PATH NOT FOUND", log_file)
            all_safe = False

    if all_safe and roots_to_flatten:
        log(f"📁 Smart-flattening {len(roots_to_flatten)} {media_type} root(s) from qBittorrent save paths...", log_file)
        if not run_windows_smart_flatten(media_type, roots_to_flatten, completed_hashes, log_file):
            if media_type in ('show', 'tv'):
                log("   ⚠️ Falling back to Python show flattener", log_file)
                flatten_errors = 0
                for root in sorted(roots_to_flatten):
                    res = flatten_show_root(root, log_file)
                    flatten_errors += int(res.get('errors', 0))
                if flatten_errors:
                    all_safe = False
            else:
                all_safe = False

    if all_safe:
        log(f"✅ Scan/flatten complete", log_file)
    else:
        log(f"⚠️ Some files failed scan or flatten - Plex refresh may have been skipped", log_file)

    log(f"🏁 Batch {batch_id} complete - exiting watcher", log_file)
    unregister_batch(batch_id)

if __name__ == "__main__":
    main()