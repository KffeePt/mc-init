#!/usr/bin/env python3
"""Tailscale homelab connector for Xan's main Hermes server.

Safety: this script does not store passwords and does not open inbound services.
It wraps Tailscale reachability checks plus SSH/SFTP/SCP commands once the target
machine has OpenSSH configured with key-based auth.
"""
from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Iterable

DEVICES = {
    "arby": {"name": "desktop-mca3em3", "ip": "100.76.137.32", "os": "windows", "role": "laptop subordinate agent"},
    "laptop": {"name": "desktop-mca3em3", "ip": "100.76.137.32", "os": "windows", "role": "laptop subordinate agent"},
    "desktop-mca3em3": {"name": "desktop-mca3em3", "ip": "100.76.137.32", "os": "windows", "role": "laptop subordinate agent"},
    "wilson": {"name": "lazarus", "ip": "100.119.118.63", "os": "windows", "role": "central commander/main desktop server"},
    "central": {"name": "lazarus", "ip": "100.119.118.63", "os": "windows", "role": "central commander/main desktop server"},
    "desktop": {"name": "lazarus", "ip": "100.119.118.63", "os": "windows", "role": "central commander/main desktop server"},
    "lazarus": {"name": "lazarus", "ip": "100.119.118.63", "os": "windows", "role": "central commander/main desktop server"},
}

DEFAULT_KEY = Path.home() / ".ssh" / "id_ed25519_tailscale_homelan"
WINDOWS_TAILSCALE = r"C:\Program Files\Tailscale\tailscale.exe"
COMMON_PORTS = [22, 445, 3389, 5985, 5986]


def run(cmd: list[str], check: bool = False) -> int:
    print("+", " ".join(str(c) for c in cmd), file=sys.stderr)
    p = subprocess.run(cmd)
    if check and p.returncode != 0:
        raise SystemExit(p.returncode)
    return p.returncode


def capture(cmd: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return p.returncode, p.stdout
    except FileNotFoundError as e:
        return 127, str(e)


def resolve(target: str) -> dict[str, str]:
    key = target.lower()
    if key in DEVICES:
        return DEVICES[key]
    # Allow raw IP/hostname for ad-hoc use.
    return {"name": target, "ip": target, "os": "unknown", "role": "ad-hoc"}


def tailscale_cmd() -> list[str] | None:
    ts = shutil.which("tailscale")
    if ts:
        return [ts]
    # WSL fallback: call Windows Tailscale through PowerShell.
    if shutil.which("powershell.exe"):
        return ["powershell.exe", "-NoProfile", "-Command", f"& '{WINDOWS_TAILSCALE}'"]
    return None


def cmd_devices(_: argparse.Namespace) -> int:
    for alias, d in DEVICES.items():
        print(f"{alias}: {d['name']} {d['ip']} {d['os']} role={d['role']}")
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    ts = tailscale_cmd()
    if not ts:
        print("tailscale CLI not found in WSL and Windows fallback unavailable", file=sys.stderr)
        return 127
    return run(ts + ["status"])


def cmd_ping(args: argparse.Namespace) -> int:
    d = resolve(args.target)
    if shutil.which("ping"):
        return run(["ping", "-c", str(args.count), "-W", str(args.timeout), d["ip"]])
    return run(["powershell.exe", "-NoProfile", "-Command", f"Test-Connection -Count {args.count} -Quiet {d['ip']}"])


def check_port(host: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def cmd_ports(args: argparse.Namespace) -> int:
    d = resolve(args.target)
    ports = args.ports or COMMON_PORTS
    for port in ports:
        state = "open" if check_port(d["ip"], int(port), args.timeout) else "closed"
        print(f"{d['name']} {d['ip']}:{port} {state}")
    return 0


def cmd_ensure_key(args: argparse.Namespace) -> int:
    key = Path(args.key).expanduser()
    pub = Path(str(key) + ".pub")
    key.parent.mkdir(parents=True, exist_ok=True)
    if key.exists() and pub.exists():
        print(f"Key already exists: {key}")
        return 0
    return run(["ssh-keygen", "-t", "ed25519", "-a", "100", "-f", str(key), "-C", "hermes-tailscale-homelan", "-N", ""], check=True)


def cmd_print_pubkey(args: argparse.Namespace) -> int:
    key = Path(args.key).expanduser()
    pub = Path(str(key) + ".pub")
    if not pub.exists():
        print(f"Missing public key: {pub}. Run ensure-key first.", file=sys.stderr)
        return 2
    print(pub.read_text().strip())
    return 0


def ssh_base(args: argparse.Namespace, d: dict[str, str]) -> list[str]:
    if not args.user:
        raise SystemExit("--user is required for SSH/SCP/SFTP operations")
    key = str(Path(args.key).expanduser())
    return [
        "ssh",
        "-i", key,
        "-o", "IdentitiesOnly=yes",
        "-o", "StrictHostKeyChecking=accept-new",
        "-o", "ConnectTimeout=10",
        f"{args.user}@{d['ip']}",
    ]


def cmd_ssh(args: argparse.Namespace) -> int:
    d = resolve(args.target)
    if not check_port(d["ip"], 22, 3):
        print(f"SSH port 22 is closed on {d['name']} ({d['ip']}). Configure OpenSSH first.", file=sys.stderr)
        return 3
    remote_cmd = args.remote_command or ["hostname"]
    return run(ssh_base(args, d) + remote_cmd)


def cmd_sftp(args: argparse.Namespace) -> int:
    d = resolve(args.target)
    if not args.user:
        print("--user is required", file=sys.stderr)
        return 2
    return run(["sftp", "-i", str(Path(args.key).expanduser()), f"{args.user}@{d['ip']}"])


def cmd_copy_to(args: argparse.Namespace) -> int:
    d = resolve(args.target)
    if not args.user:
        print("--user is required", file=sys.stderr)
        return 2
    src = args.source
    dst = f"{args.user}@{d['ip']}:{args.destination}"
    return run(["scp", "-i", str(Path(args.key).expanduser()), "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=accept-new", "-r", src, dst])


def cmd_copy_from(args: argparse.Namespace) -> int:
    d = resolve(args.target)
    if not args.user:
        print("--user is required", file=sys.stderr)
        return 2
    src = f"{args.user}@{d['ip']}:{args.source}"
    return run(["scp", "-i", str(Path(args.key).expanduser()), "-o", "IdentitiesOnly=yes", "-o", "StrictHostKeyChecking=accept-new", "-r", src, args.destination])


def cmd_setup_openssh_windows(args: argparse.Namespace) -> int:
    d = resolve(args.target)
    print(f"Target: {d['name']} {d['ip']} ({d['role']})")
    print("Run these on the target Windows machine in an elevated PowerShell window:")
    print(r'''
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Set-Service -Name sshd -StartupType Automatic
Start-Service sshd
New-NetFirewallRule -Name 'OpenSSH-Server-In-TCP-Tailscale' -DisplayName 'OpenSSH Server over Tailscale' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 -Profile Private
$sshDir = Join-Path $HOME '.ssh'
New-Item -ItemType Directory -Force -Path $sshDir | Out-Null
notepad (Join-Path $sshDir 'authorized_keys')
'''.strip())
    print("\nPaste this public key into authorized_keys:")
    return cmd_print_pubkey(args)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Operate Xan's Tailscale homelab from the main Hermes server")
    p.set_defaults(func=lambda args: p.print_help() or 0)
    sub = p.add_subparsers(dest="command")

    sp = sub.add_parser("devices", help="List known device aliases")
    sp.set_defaults(func=cmd_devices)

    sp = sub.add_parser("status", help="Show tailscale status via local/Windows CLI")
    sp.set_defaults(func=cmd_status)

    sp = sub.add_parser("ping", help="Ping a known target")
    sp.add_argument("target")
    sp.add_argument("--count", type=int, default=2)
    sp.add_argument("--timeout", type=int, default=2)
    sp.set_defaults(func=cmd_ping)

    sp = sub.add_parser("ports", help="Check common remote admin/file-transfer ports")
    sp.add_argument("target")
    sp.add_argument("--ports", type=int, nargs="*")
    sp.add_argument("--timeout", type=float, default=2.0)
    sp.set_defaults(func=cmd_ports)

    sp = sub.add_parser("ensure-key", help="Create the homelab SSH key if missing")
    sp.add_argument("--key", default=str(DEFAULT_KEY))
    sp.set_defaults(func=cmd_ensure_key)

    sp = sub.add_parser("print-pubkey", help="Print the public key to install on targets")
    sp.add_argument("--key", default=str(DEFAULT_KEY))
    sp.set_defaults(func=cmd_print_pubkey)

    sp = sub.add_parser("setup-openssh-windows", help="Print target-side Windows OpenSSH setup commands")
    sp.add_argument("target")
    sp.add_argument("--key", default=str(DEFAULT_KEY))
    sp.set_defaults(func=cmd_setup_openssh_windows)

    sp = sub.add_parser("ssh", help="Run a command on a target over SSH")
    sp.add_argument("target")
    sp.add_argument("--user")
    sp.add_argument("--key", default=str(DEFAULT_KEY))
    sp.add_argument("remote_command", nargs=argparse.REMAINDER)
    sp.set_defaults(func=cmd_ssh)

    sp = sub.add_parser("sftp", help="Open interactive SFTP to target")
    sp.add_argument("target")
    sp.add_argument("--user")
    sp.add_argument("--key", default=str(DEFAULT_KEY))
    sp.set_defaults(func=cmd_sftp)

    sp = sub.add_parser("copy-to", help="Copy local path to target over SCP")
    sp.add_argument("target")
    sp.add_argument("--user")
    sp.add_argument("--key", default=str(DEFAULT_KEY))
    sp.add_argument("source")
    sp.add_argument("destination")
    sp.set_defaults(func=cmd_copy_to)

    sp = sub.add_parser("copy-from", help="Copy target path to local destination over SCP")
    sp.add_argument("target")
    sp.add_argument("--user")
    sp.add_argument("--key", default=str(DEFAULT_KEY))
    sp.add_argument("source")
    sp.add_argument("destination")
    sp.set_defaults(func=cmd_copy_from)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
