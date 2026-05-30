# 2026-05-26 — qBittorrent Hook Scripts Belong in Hermes Workspace

## Trigger

Use this when Xan asks for qBittorrent/Plex automation scripts, media lifecycle hooks, or asks to move ad-hoc scripts into the shared Hermes workspace so other agents can find them.

## Rule

Persistent user-facing automation scripts should live under:

```text
C:\Users\santi\Documents\Hermes\Scripts\
/mnt/c/Users/santi/Documents/Hermes/Scripts/
```

Avoid leaving durable scripts only in drive-root utility folders such as `D:\Scripts\` when the script is meant to be shared across Wilson/Arby/Lazarus/LilJon or referenced by future agents.

## qBittorrent hook implication

When moving qBittorrent hook scripts:

1. Move/copy the scripts into the Hermes Scripts directory.
2. Update qBittorrent GUI hook commands to point at the new Windows path.
3. Update any skill/reference text that contains paste-ready hook commands.
4. Verify the PowerShell scripts still parse from the new location.
5. Trigger or simulate the hook if safe, then verify log/state output.

Example path shape:

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\santi\Documents\Hermes\Scripts\qbittorrent-on-added.ps1" "%F" "%N" "%L" "%D"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\santi\Documents\Hermes\Scripts\qbittorrent-on-finished.ps1" "%F" "%N" "%L" "%D"
```

## Pitfall

If the user says “move the scripts and update the skills,” do not only update chat instructions. Actually move the files, patch the relevant media/download skill(s), and provide the new paste-ready commands. A script path mismatch in qBittorrent is silent failure wearing a hat.
