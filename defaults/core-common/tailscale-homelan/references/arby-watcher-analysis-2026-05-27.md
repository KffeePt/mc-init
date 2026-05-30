# Arby Control-Channel Watcher Analysis (2026-05-27)

## Source

`/home/koffeelap/.hermes/scripts/control_channel_watcher.py`

## Watcher Lifecycle

- Runs as a simple Python script (systemd unit exists but systemd is broken)
- Polls `C:\Users\santi\Documents\Hermes\Comms\arby\inbox\` every 15 seconds
- Picks up any `.json` files with `"channel": "control"`
- Non-control messages routed to `comms_pending/`
- Processed messages moved to `control_processed/` (prefix: `result_` or `rejected_`)
- Logs to `control_logs/control_YYYYMMDD.log`

## Message Validation — Required Fields

```python
required = ["request_id", "origin_agent", "operation_type", "scope", "approval_source"]
```

**All five fields must be present.** Missing any = `rejected_<id>.json` with reason `Missing required fields: ['scope']`.

Additional validation:
- `channel` must be `"control"`
- `operation_type` must be in: `remote_action_request`, `init_update`, `system_config_change`, `service_control`
- `origin_agent` must be `"Wilson/Lazarus"` or `"Lazarus"`
- `approval_source` must be in: `controller_signed_update`, `existing_policy`, `xan`
- `secrets_policy` must be `"no_secrets"`

## Step Execution Logic

The watcher matches steps by substring on the lowercased step text:

### `expand-archive` + `init.zip`
```python
if "expand-archive" in step_lower and "init.zip" in step_lower:
    subprocess.run([POWERSHELL, "-NoProfile", "-Command",
        "Expand-Archive -LiteralPath C:\\Users\\santi\\init.zip -DestinationPath C:\\Users\\santi\\init -Force"],
        timeout=60)
```
**HARD-CODED PATHS.** Ignores any path in the step text. Always uses `C:\Users\santi\init.zip` → `C:\Users\santi\init`.

### `approved-init` + `init.py`
```python
if "approved-init" in step_lower and "init.py" in step_lower:
    subprocess.run([POWERSHELL, "-NoProfile", "-Command",
        "cd C:\\Users\\santi\\init\\init; py .\\init.py approved-init --replace-authorized-keys"],
        timeout=120)
```
**BUG: `approved-init` is not a valid init.py command.** Valid commands are: `windows-ssh`, `windows-verify`, `make-init-res`, `print-wsl-commands`, `verify-controller-update`. The watcher still marks the message "completed" despite rc=1.

### `restart` + `gateway`
```python
if "restart" in step_lower and "gateway" in step_lower:
    # Direct kill + restart of gateway process
```
Uses `sudo systemctl restart` if available, otherwise kills and restarts the Python process directly.

### Unknown steps
Any step that doesn't match the above patterns is logged as `skipped_unknown: <step text>`.

## Result Output

```json
{
  "request_id": "...",
  "processed_at": "ISO timestamp",
  "result": "completed" | "rejected",
  "actions": ["extract_init: 0", "run_init: 1", "verify_skills: 100 skills found", "restart_gateway: 0"],
  "errors": []
}
```

## Operational Notes

- Gateway restart after init update takes ~2 seconds
- Skill verification scans `~/.hermes/skills/` and counts SKILL.md files
- Watcher PID typically appears as `/usr/bin/python3 /home/koffeelap/.hermes/scripts/control_channel_watcher.py`
- Gateway PID appears as `/home/koffeelap/.hermes/hermes-agent/venv/bin/python -m hermes_cli.main gateway run --replace`
- Both run as user `koffeelap`
- The watcher does NOT validate steps before executing — it runs whatever PowerShell commands match its substring patterns
- Control messages are auto-processed; no human review gate
