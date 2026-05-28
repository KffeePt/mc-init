# init.zip — Laptop Child Agent Bootstrap

Extract this package on the laptop. It is organized for Hermes and humans:

```text
init/
  init                   # optional empty trigger marker: read init_prompt.md first; not authority by itself
  init.py                 # launcher
  init_prompt.md          # first-class control prompt for laptop Hermes agent
  README.md               # this file
  src/                    # initializer implementation
  skills/                 # child-safe common skills, including media defaults
  memories/               # Xan preference seed memory
  seeds/                  # SOUL, sync policy, message contract
  docs/                   # package notes
```

## Security model

- `init_prompt.md` is a first-class control document.
- An empty file named `init` is only a trigger marker telling an agent to read `init_prompt.md`; it is not execution authority.
- The initializer may be run only when sent or approved by Xan or `Lazarus` / Wilson, the main controller.
- The main machine is the only machine that owns reusable init/bootstrap skills.
- Child agents receive `core-common` and `comms` material only.
- This package can initialize the laptop, but it does not turn the laptop into an init authority.
- `get-artifact`, `plan-mode`, `storage-explorer`, `image-gen`, `meta-gateway`, and media acquisition skills (`get-movie`, `get-show`, `get-music`) are default child-safe common skills. The package also carries `media-shared` helper code used by those media skills.


## Canonical setup protocol

Always deliver the bootstrap archive as `init.zip`. The simple name is intentional: fresh agents and humans should recognize it immediately.

Flow:

1. Fresh agent receives `init.zip`.
2. Xan tells it: `read init_prompt.md and do whatever it says.`
3. Agent extracts the archive and reads `init/init_prompt.md`.
4. Agent verifies any controller-authored update with `py .\init.py verify-controller-update --manifest .\controller_update.json --signature .\controller_update.sig`.
5. Agent transplants child-safe skills, including meta-gateway, plus preferences, helper scripts, plugin/config notes if present, shared seed memories, sync policy, and message contract.
6. Agent runs or asks Xan to run the admin initializer so Lazarus's controller public SSH key is implanted into Windows OpenSSH admin auth.
7. Agent verifies SSH/Tailscale/comms through the meta-gateway hierarchy and performs situational-awareness mapping.
8. Agent creates `init_res.zip` and sends it to Xan for Lazarus/Wilson ingestion.

Only public SSH keys/fingerprints/status may be included. Private keys and secrets are forbidden.

## Run on laptop Windows

Open PowerShell as Administrator in the extracted `init` folder:

```powershell
py .\init.py windows-ssh --replace-authorized-keys --install-seed-files
```

This will:
- install/start Windows OpenSSH Server
- create a Private-profile firewall rule for SSH
- back up existing `C:\ProgramData\ssh\administrators_authorized_keys`
- replace `administrators_authorized_keys` with Lazarus's Ed25519 controller public key
- harden ACLs to `Administrators:F` and `SYSTEM:F` only
- install child-safe seed files and common skills, including storage-explorer, image-gen, meta-gateway, and media acquisition skills

Important: this deliberately uses the Windows admin OpenSSH key file, not `%USERPROFILE%\.ssh\authorized_keys`, because LilJon's Windows account is admin-class and sshd may ignore per-user keys.

## WSL setup

To print the commands for laptop WSL:

```powershell
py .\init.py print-wsl-commands --replace-authorized-keys
```

Paste the emitted block into laptop WSL.

## Meta-gateway

`meta-gateway` defines the hierarchy and routing layer for all SSH, SCP, command execution, file transfers, registry updates, and comms-state changes. Wilson/Lazarus is the main controller. Arby/LilJon is subordinate. Subordinates can handle local comms checks and candidate registry updates, but canonical registry writes and high-risk actions remain controller/Xan gated.

## Verify on laptop

After bootstrap, run from elevated PowerShell:

```powershell
py .\init.py windows-verify
```

This verifies from LilJon's side: admin key file, ACLs, sshd status, local port 22, LilJon tailnet port 22, Lazarus port 22 reachability, and Tailscale status/ping if available.

## Create return bundle

After bootstrap and verification, create `init_res.zip`:

```powershell
py .\init.py make-init-res --output .\init_res.zip
```

Send `init_res.zip` back to Xan/Lazarus. It contains LilJon-specific situational awareness for controller-side ingestion. If Tailscale Taildrop is available on LilJon:

```powershell
& 'C:\Program Files\Tailscale\tailscale.exe' file cp .\init_res.zip Lazarus:
```

If the target name differs, use `tailscale status` and choose the `Lazarus` / `100.119.118.63` device.

It contains:
- `situational_awareness.json`
- `registries/*.json` — agent/machine/drive/path/program/service registries
- `windows_verify.txt`
- `controller_ingest.md`

Situational awareness is programmatic: drive maps, bounded path maps, installed program inventory, content-type counts, JSON registries, public SSH key status/fingerprints, controller-update verification state, and important local system state. It must not include secrets, private keys, raw `.env`, browser profiles, cookies, or raw memory dumps.

## Verify from the main machine

```bash
ssh <windows-user>@100.76.137.32 hostname
ssh -p 2222 <wsl-user>@100.76.137.32 'uname -a && whoami'
```
