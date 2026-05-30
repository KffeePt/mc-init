# Lazarus → LilJon Windows OpenSSH Admin-Key Fix

## Context

Use this reference when Lazarus/Wilson can reach LilJon/Arby over Tailscale and port 22 is open, but SSH rejects the controller key with `Permission denied (publickey,password,keyboard-interactive)`.

Current names:

- `Lazarus` — Wilson's body / main controller / `100.119.118.63`
- `LilJon` — Arby's body / laptop child machine / hostname `desktop-mca3em3` / `100.76.137.32`

## Durable lesson

On Windows OpenSSH, administrator-class accounts commonly authenticate through:

```text
C:\ProgramData\ssh\administrators_authorized_keys
```

not through:

```text
C:\Users\<user>\.ssh\authorized_keys
```

If the bootstrap writes only the per-user file, port 22 can be reachable while every tested admin username rejects the key. Do not churn through usernames before checking the admin key file.

## Correct Lazarus controller key

Use Lazarus's Ed25519 Tailscale/home-LAN key:

```text
/home/xantastique/.ssh/id_ed25519_tailscale_homelan.pub
```

Expected public key label:

```text
hermes-tailscale-homelan
```

Do not use the older RSA key for this path unless Xan explicitly chooses that key.

## Manual fix on LilJon

Run in elevated PowerShell on LilJon:

```powershell
$pubkey = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFN30tVz4lgsj9GViTQK1EoRzYoAemvjWZIQ4sxrL48I hermes-tailscale-homelan'
$adminKeys = 'C:\ProgramData\ssh\administrators_authorized_keys'

New-Item -ItemType File -Force -Path $adminKeys | Out-Null
if (Test-Path $adminKeys) {
  Copy-Item $adminKeys "$adminKeys.bak.$(Get-Date -Format yyyyMMddHHmmss)" -ErrorAction SilentlyContinue
}
Set-Content -Path $adminKeys -Value $pubkey -Encoding ascii

icacls $adminKeys /inheritance:r
icacls $adminKeys /grant 'Administrators:F' /grant 'SYSTEM:F'
icacls $adminKeys /remove 'Users' 'Authenticated Users' 'Everyone'
Restart-Service sshd
```

## Verification from Lazarus

```bash
ssh -i ~/.ssh/id_ed25519_tailscale_homelan <windows-user>@100.76.137.32 hostname
```

If that succeeds, verify identity and command context:

```bash
ssh -i ~/.ssh/id_ed25519_tailscale_homelan <windows-user>@100.76.137.32 'hostname && whoami'
```

## Init package rule

Any future LilJon/Windows-child init package should default to:

1. Ed25519 `id_ed25519_tailscale_homelan.pub`
2. `C:\ProgramData\ssh\administrators_authorized_keys`
3. strict admin ACLs only
4. backup before replace
5. restart `sshd`
6. controller-side SSH verification

The reusable init authority remains on Lazarus. LilJon may run a one-time extracted init package, but should not receive reusable init/bootstrap skills by default.
