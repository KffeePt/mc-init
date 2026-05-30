# Wilson / Arby Tailnet Verification — 2026-05-25

Session-specific detail for the class-level `tailscale-homelan` workflow.

## Machine Roles

- Wilson / central: `lazarus`, Windows, tailnet IP `100.119.118.63`.
- Arby / laptop subordinate: `desktop-mca3em3`, Windows, tailnet IP `100.76.137.32`.
- Tailnet: `kffeept.github`.

## Verified Live State

- Tailscale status showed both machines online.
- Wilson -> Arby Tailscale ping succeeded.
- WSL ICMP ping to Arby succeeded with 0% packet loss.
- Arby ports:
  - `22` SSH open.
  - `445` SMB open.
  - `3389` RDP closed.
  - `5985/5986` WinRM closed.
- Wilson/lazarus ports over tailnet:
  - `445` SMB open.
  - `22` SSH closed.

## Command Access Finding

SSH transport to Arby exists, but Wilson was not authorized yet. Attempts using likely Windows usernames reached the SSH server and failed with:

```text
Permission denied (publickey,password,keyboard-interactive)
```

Interpretation: this is an auth/configuration gap, not a network discovery failure.

## File Transfer Finding

Wilson sent a benign verification file to Arby using Tailscale Taildrop:

```bash
tailscale file cp <verification-file> desktop-mca3em3:
```

The sender-side transfer exited successfully. This proves Wilson can hand a file to the Tailscale file-transfer channel for Arby. It does **not** prove content-level receipt unless Arby inspects its Taildrop inbox or sends a return file.

## Durable Procedure Lesson

When verifying bidirectional machine control, separate four layers explicitly:

1. Discovery: both nodes appear in `tailscale status`.
2. Reachability: `tailscale ping`, ICMP ping, and port checks.
3. Authenticated command path: SSH command succeeds with `hostname && whoami`.
4. Content-level transfer proof: checksum-matched file round trip.

Do not claim full two-way control until layers 3 and 4 pass in both directions.

## Next Actions To Complete Control

1. Install Wilson's homelab public key in Arby's Windows user `authorized_keys`.
2. Verify Wilson -> Arby command execution:

```bash
python3 ~/.hermes/skills/devops/tailscale-homelan/scripts/tailscale_homelan.py ssh arby --user <windows-user> -- 'hostname && whoami'
```

3. Verify SCP round trip with hashes.
4. Only enable Wilson/lazarus inbound SSH if Xan explicitly wants Arby -> Wilson direct command access. Central remote-admin exposure should be deliberate, not incidental.
