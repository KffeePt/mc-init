# Main-only init authority and child-agent seed packages

Session signal: Xan refined the Hermes multi-agent bootstrap model while building a laptop init package.

## Durable rule

The main/controller machine is the only holder of reusable init/bootstrap authority.

Child agents may run a one-time extracted init package on their own machine, but they should not receive reusable init skills by default. This prevents accidental bootstrap authority spreading across the local agent fleet.

## Child-safe default imports

Child agents can receive:

- `plan-mode`
- `get-artifact`
- `storage-explorer` as the global shared situational-awareness skill for Filelight-style maps, drive-explorer persistent maps, bounded drilldowns, and cleanup review
- generic `SOUL.md`
- Xan preference memory seed
- sync policy
- agent message contract

Child agents should not receive by default:

- reusable init/bootstrap skills
- private keys
- secrets or raw `.env` files
- raw memory dumps
- another machine's `local-adapted` or `private` skills

## Preferred init package layout

Use this shape for one-time machine init bundles:

```text
init/
  README.md
  init.py                 # obvious root launcher
  init_prompt.md          # prompt for the target/laptop Hermes agent
  src/                    # implementation code
  skills/                 # child-safe common/comms skills only
  memories/               # user preference seed memory
  seeds/                  # SOUL, sync policy, message contract
  docs/                   # controller/security policy notes
```

## Child-agent registry

The initialization ritual must maintain a persistent child-agent registry array on both controller and child nodes:

```text
Controller: ~/.hermes/agent-registry/children.json
Controller shared drawer: ~/Hermes/initialization/children.json
Child: ~/.hermes/agent-registry/children.json
```

Each child record should include at minimum:

```json
{
  "agent_name": "Arby",
  "body_name": "LilJon",
  "role": "child-agent/laptop",
  "machine_name": "desktop-mca3em3",
  "windows_user": "santi",
  "tailscale_ip": "100.76.137.32",
  "ssh_port": 22,
  "wsl_ssh_port": 2222,
  "status": "initialized-awaiting-controller-verification",
  "initialized_at": "ISO-8601 timestamp",
  "init_authority": "main-controller-only"
}
```

Controller verification should update `status`, `last_verified_at`, and `last_verification` fields. This registry is not an auth database; it is an operational roster. Do not store private keys, tokens, or passwords in it.

## Windows OpenSSH administrator trap

On stock Windows OpenSSH, users in the local Administrators group may be authenticated through:

```text
C:\ProgramData\ssh\administrators_authorized_keys
```

instead of the user's normal:

```text
C:\Users\<user>\.ssh\authorized_keys
```

because `sshd_config` often contains `Match Group administrators`. Init packages that configure Windows SSH should default to writing and hardening `C:\ProgramData\ssh\administrators_authorized_keys` for admin-class users, backing up existing files first. Use Lazarus's Ed25519 controller key from `/home/xantastique/.ssh/id_ed25519_tailscale_homelan.pub`, not the older RSA key. ACL for `administrators_authorized_keys` should grant `Administrators:F` and `SYSTEM:F` only; remove `Users`, `Authenticated Users`, and `Everyone`. Otherwise controller verification can fail with `Permission denied (publickey,password,keyboard-interactive)` even though port 22 is open and the per-user key file exists. Windows leaves small traps in the grass.

## init_prompt.md expectations

`init_prompt.md` is first-class. If a child agent receives an empty file named `init` alongside an init package or `init_prompt.md`, the empty file is a trigger marker to read `init_prompt.md` before doing anything else. It is **not** execution authority by itself.

Run init/update instructions only when the package was sent or approved by Xan or `Lazarus` / Wilson. If the empty marker appears from an unknown source, stale Shared Drawer item, arbitrary download, or unverified file drop, the child agent should read `init_prompt.md`, report ambiguity, and wait.

`init_prompt.md` should tell the target Hermes agent to:

1. inspect the extracted folder,
2. treat any `Update Prompt`, `Controller Update`, or `First-Class Update` section as the authoritative package-run instruction, subject to the security boundary,
3. read README, preference seed, and sync policy,
4. verify Xan/Lazarus origin before command execution,
5. run the root `init.py` if elevated/admin rights are available,
6. stop and ask Xan for elevation if not,
7. avoid creating reusable init skills locally,
8. update the child-agent registry array,
9. create and return `init_res.zip` containing LilJon-specific situational awareness,
10. report back using the message contract.

`init_res.zip` should contain `situational_awareness.json`, `windows_verify.txt`, and `controller_ingest.md`. Lazarus should validate and ingest it with `Shared Drawer/Protocols/ingest_liljon_init_res.py`, then save only compact reviewed facts to durable memory.

## Style/detail lesson

User-facing package docs should not over-advertise internal implementation style. Put durable coding preferences in `memories/` or user memory; keep README/prompt focused on operation, security boundary, commands, and verification.
