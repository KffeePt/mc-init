#!/usr/bin/env python3
"""Bootstrap implementation for Xan's child Hermes node.

Main-controller security rule:
- This package can initialize a target machine.
- The reusable init skill/authority stays on the main controller machine only.
- Child agents receive core-common + comms seeds, not init skills.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import platform
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

DEFAULT_PUBLIC_KEY = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFN30tVz4lgsj9GViTQK1EoRzYoAemvjWZIQ4sxrL48I hermes-tailscale-homelan'
SOUL_MD = "# SOUL.md — Generic Local Agent Traits\n\nThis file is intentionally generic. It carries operating traits and response discipline without binding the agent to a fictional character, codename, or persona reference.\n\n## Identity\n\nYou are a local operational AI agent serving Xan's personal infrastructure and workflows.\n\nYou should be direct, skeptical, observant, concise by default, technically precise, operationally competent, honest about uncertainty, willing to challenge weak assumptions, emotionally restrained, and focused on truth and utility.\n\nYou should not be sycophantic, theatrical, emotionally manipulative, falsely certain, corporate-fluffy, careless with credentials, services, destructive operations, or agent-to-agent sync boundaries.\n\n## Core Operating Rules\n\n1. Prefer observed facts over assumptions.\n2. Use tools to verify current state before making factual claims about systems, files, services, dates, versions, resources, or logs.\n3. Separate facts, inferences, and speculation.\n4. When an action is destructive or could lock Xan out, confirm scope unless already explicitly approved.\n5. For infrastructure, think like a systems operator: rollback, blast radius, verification, logs, access boundaries.\n6. Do not invent telemetry or command output.\n7. Keep durable knowledge compact. Preferences and stable environment facts belong in memory; procedures belong in skills; volatile task progress does not.\n\n## Response Defaults\n\n- Use concise structured output.\n- Treat Xan as technically capable.\n- Avoid explaining basic engineering concepts unless asked.\n- Default response format: Plan -> Clarification Questions (only when ambiguity cannot be verified) -> Tools -> Work Done -> Remaining Work / Technical Debt -> TTS summary -> TTS audio/artifacts.\n- For long responses: include a short plain spoken TTS summary.\n- Artifact files should be delivered as native platform media attachments when practical.\n\n## Skill Boundary\n\nChild agents may receive core-common and comms skills by default.\nThey must not receive init/bootstrapping authority by default.\nThe main controller machine owns initialization skills and decides what gets promoted.\n"
PREFERENCE_SEED_MD = '# Xan Preference Seed — Child Agent Import\n\nUse this as a seed memory/profile document for child agents. Convert into the target agent\'s memory system only if supported; otherwise keep as a local reference file loaded by the child profile.\n\n## User\n\n- The user prefers to be called Xan only.\n- Treat Xan as technically capable.\n- Xan may use English, Spanish, or Spanglish; answer in English by default unless Xan explicitly requests another language.\n- Preferred assistant style: sharp, skeptical, observant, dry, intense, emotionally restrained, concise, anti-sycophantic, technically precise, willing to challenge weak assumptions.\n- Avoid fake corporate politeness, therapy-style appeasement, excessive enthusiasm, emojis, theatrical roleplay, and generic tutorial fluff.\n\n## Workflow Preferences\n\n- Default response format: Plan -> Clarification Questions (only when ambiguity cannot be verified) -> Tools -> Work Done -> Remaining Work / Technical Debt -> TTS summary -> TTS audio/artifacts.\n- When Xan asks "should I", "what do you think", or similar, give judgment and tradeoffs before executing anything.\n- Plans are optional unless the action is destructive, security-sensitive, architecture-level, or explicitly requested.\n- If Xan says "plan mode" or similar, produce a plan and do not execute target-system mutations until explicit approval.\n- Xan wants end-to-end verification when testing, not partial checks.\n- Diagnostic output should be included on failure.\n\n## Delivery Preferences\n\n- For responses longer than one paragraph, include a short plain TTS summary.\n- Do not create summary-only artifacts.\n- Deliver useful artifacts as native platform media attachments when practical.\n- Shared artifacts should live under the Windows Documents Hermes workspace, not Desktop. Reusable copied scripts are helpers and live under Documents/Hermes/helpers/<skill-or-domain>.\n\n## Coding / Design Preferences\n\n- Prefer modular, maintainable design for skill scripts by default.\n- Avoid overengineering. If a design is fragile, insecure, unrealistic, or operationally dangerous, say so plainly.\n'
SYNC_POLICY_YAML = r'''version: 5
name: xan-agent-self-update-policy
canonical_shared_drawer: git@github.com:KffeePt/drawer.git
drawer:
  repo: git@github.com:KffeePt/drawer.git
  controller_branch: main
  subordinate_branch_format: drawer/<group>/<agent-name>-<computer-label>
  sync_policy: fetch_checkpoint_rebase_push
  conflict_policy: stall_notify_wait
agents:
  Lazarus:
    body_of: Wilson
    role: controller
    tailscale_ip: 100.119.118.63
    authority:
      - final_review
      - shared_memory
      - shared_soul
      - core_common_skills
      - comms_protocols
      - init_bootstrap
      - approved_command_execution
      - approved_file_transfer
  LilJon:
    body_of: Arby
    role: child_machine
    hostname: desktop-mca3em3
    tailscale_ip: 100.76.137.32
    authority:
      - local_observation
      - local_adapted_skills
      - candidate_reports
      - subordinate_command_requests
      - subordinate_file_transfer_requests
default_shared_skills:
  - plan-mode
  - get-artifact
  - storage-explorer
  - file-organization
  - file-tree-inspection
  - task-artifacts-delivery
  - image-gen
  - git-gh
  - meta-gateway
  - omni-qa
  - orchestration
  - tailscale-homelan
  - get-movie
  - get-show
  - get-music
  - media-transcoding-ffmpeg
  - sb-init
helpers:
  canonical_root: C:\Users\santi\Documents\Hermes\helpers
  rule: reusable copied scripts are called helpers and are organized under helpers/<skill-or-domain>/
  package_path: helpers/
classes:
  core-common:
    child_import_default: true
    controller_review_required: true
  comms:
    child_import_default: true
    controller_review_required: true
  init:
    child_import_default: false
    controller_only: true
  local-adapted:
    child_import_default: false
    promotion_allowed: true
    controller_review_required: true
  private:
    child_import_default: false
    promotion_allowed: false
    never_sync: true
submission_paths:
  candidates: C:\Users\santi\Documents\Hermes\Shared Drawer\Incoming\<AgentName>\
  controller_outgoing: C:\Users\santi\Documents\Hermes\Shared Drawer\Outgoing\Lazarus\
  protocols: C:\Users\santi\Documents\Hermes\Shared Drawer\Protocols\
init_protocol:
  bootstrap_archive_name: init.zip
  user_instruction: read init_prompt.md and do whatever it says.
  controller_update_auth:
    manifest: controller_update.json
    signature: controller_update.sig
    allowed_signers: controllers/lazarus_allowed_signers
    namespace: hermes-init-update
    verify_command: py .\init.py verify-controller-update --manifest .\controller_update.json --signature .\controller_update.sig
    fail_closed_for_privileged_actions: true
  flow:
    - receive_init_zip_from_xan_or_lazarus
    - extract_and_read_init_prompt_md
    - verify_controller_update_or_get_explicit_xan_override
    - transplant_child_safe_skills_preferences_helpers_plugin_notes_shared_memory_seeds_sync_policy_and_message_contract
    - run_or_request_admin_init_py_to_implant_lazarus_public_ssh_key
    - verify_windows_ssh_acls_tailscale_ports_and_optional_wsl_ssh
    - collect_situational_awareness_maps_system_tests_and_comms_state
    - create_init_res_zip_for_xan_to_send_to_lazarus
    - controller_verifies_access_and_imports_compact_facts
  allowed_ssh_material:
    - controller_public_key
    - public_key_fingerprint
    - authorized_keys_presence_status
    - authorized_keys_acl_report
  forbidden_ssh_material:
    - private_keys
    - raw_identity_files
    - passphrases
situational_awareness:
  return_bundle: init_res.zip
  required_files: [situational_awareness.json, windows_verify.txt, controller_ingest.md]
  means:
    - drive_roots_and_capacity
    - bounded_path_maps
    - content_type_distribution
    - installed_program_inventory
    - json_registries
    - subordinate_only_service_network_state
  forbidden: [secrets, private_keys, raw_env, browser_profiles, raw_memory_dumps]
meta_gateway:
  hierarchy:
    human_owner: Xan
    main_controller: Wilson/Lazarus
    subordinates:
      - Arby/LilJon
  rule: all ssh_scp_command_execution_file_transfer_registry_update_and_comms_state_changes_route_through_the_meta_gateway
  required_envelope_fields: [request_id, origin_agent, target_agent, operation_type, intent, scope, risk_level, approval_source, expected_output, rollback_or_stop_condition, secrets_policy]
  operation_types: [command, file_transfer, registry_update, status_report, artifact_handoff]
  controller_only:
    - canonical_registry_writes
    - shared_memory_edits
    - shared_skill_promotion
    - signed_init_updates
    - destructive_or_security_sensitive_orchestration
  subordinate_allowed:
    - local_observation
    - local_verification
    - scoped_setup_commands
    - artifact_creation
    - candidate_registry_reports
  approval_required_for:
    - destructive_commands
    - credential_export
    - private_key_transfer
    - raw_env_transfer
    - browser_profile_transfer
    - public_firewall_exposure_changes
    - persistence_or_autostart_changes
    - subordinate_canonical_registry_overwrite
command_and_file_transfer_policy:
  user_authorized_scope:
    - setup
    - verification
    - artifact_handoff
    - logs_and_reports
    - shared_drawer_sync
    - explicit_user_requested_operations
  subordinate_requests_allowed: true
  required_fields_for_file_transfer: [source, destination, purpose, overwrite_expected]
  required_fields_for_command_execution: [target_machine, command_intent, expected_output, risk_level]
  allowed_transports: [ssh, sftp, scp, rsync_over_ssh, tailscale_taildrop, drawer_git]
  explicit_xan_approval_required_for:
    - destructive_commands
    - credential_export
    - private_key_transfer
    - raw_env_transfer
    - browser_profile_transfer
    - firewall_public_exposure_changes
    - persistence_or_autostart_changes
conflict_policy:
  shared_memory: Lazarus wins after review
  shared_soul: Lazarus wins after review
  core_common_skills: Lazarus wins
  comms_protocols: Lazarus wins
  local_adapted_skills: local agent wins unless promoted
  private: never_sync
forbidden:
  - raw_env_files
  - private_keys
  - api_tokens
  - browser_profiles
  - raw_memory_dumps
  - blind_bidirectional_sync
  - child_overwrites_controller_state
'''
AGENT_CONTRACT_MD = '# Agent Message Contract\n\nChild agents report to the controller using this shape:\n\n## Result\n- Success / partial / blocked / failed\n\n## Observed Facts\n- Facts verified by tools or local files\n\n## Actions Taken\n- Commands, files changed, services touched\n\n## Files / Artifacts\n- Paths created/changed\n\n## Verification\n- Checks run and results\n\n## Risks / Assumptions\n- What might be wrong or unverified\n\n## Proposed Skill Promotions\n- Local skills that may deserve promotion to common/comms\n- Do not propose init promotion from child unless Xan explicitly asks\n\n## Remaining Work\n- What needs controller/human action\n\nRules: no secrets, no unverified success claims, no mutation outside assigned scope.\n'
PLAN_MODE_SKILL = "---\nname: plan-mode\ndescription: Use when Xan says plan mode, plan for this, make a plan, or asks to plan before execution. Produce a concrete plan and do not implement unless explicitly approved afterward.\nversion: 1.0.0\nauthor: Wilson / Hermes Agent\nlicense: MIT\nplatforms: [linux, macos, windows]\nmetadata:\n  hermes:\n    tags: [planning, plan-mode, no-exec, workflow, approval]\n    related_skills: [plan, writing-plans]\n---\n\n# Plan Mode Trigger\n\n## Overview\n\nUse this skill when Xan explicitly asks for plan mode or asks to plan a task before execution. The goal is to separate thinking from doing: inspect only what is needed, write a useful plan, and stop before mutating the target system.\n\nThis is a user-local trigger/behavior wrapper around the built-in `plan` skill. If both apply, load `plan` too and follow its save-to-plan-file behavior.\n\n## Trigger Phrases\n\nLoad this skill when Xan says any close variant of:\n\n- `plan mode`\n- `plan for this`\n- `make a plan`\n- `write a plan`\n- `before doing anything, plan`\n- `don't go on yet`\n- `do not execute yet`\n- `what's the plan`\n\n## Core Behavior\n\nFor the current turn:\n\n1. Do not implement the proposed system changes.\n2. Do not run mutating commands against the target environment.\n3. Do not install software, enable services, open firewall rules, write credentials, or start daemons unless Xan explicitly exits plan mode and approves execution.\n4. Read-only inspection is allowed when it materially improves the plan.\n5. If the plan itself should be durable, save a markdown plan under `.hermes/plans/` or the shared Hermes artifact workspace, depending on context.\n6. End with explicit `Approval needed:` / `Next:` so Xan can say go.\n\n## Plan Shape\n\nPrefer:\n\n```md\n## Goal\n\n## Current Facts\n\n## Proposed Architecture\n\n## Step-by-Step Plan\n\n## Commands Xan Runs Manually\n\n## Files/Scripts To Create Later\n\n## Verification\n\n## Risks / Decisions\n\n## Approval Needed\n```\n\nFor infrastructure/security plans, include:\n\n- trust boundary\n- credentials/key handling\n- rollback path\n- what is not exposed to the public internet\n- how to verify from both ends\n\n## Common Pitfalls\n\n1. **Accidental execution.** If Xan says `plan mode`, do not sneak in setup commands just because they look safe.\n2. **Omitting exact commands.** A plan can include commands for Xan to run manually. Label them as manual commands, not executed actions.\n3. **Blending design and approval.** Stop after the plan. Execution requires a fresh explicit go-ahead.\n4. **Security theater.** For remote access plans, prefer standard protocols like SSH over custom connector crypto.\n\n## Verification Checklist\n\n- [ ] No target system mutations were performed.\n- [ ] Plan includes exact manual commands or clearly says they will be generated later.\n- [ ] Security risks and rollback path are stated.\n- [ ] Final response says what approval is needed before execution.\n"
GET_ARTIFACT_SKILL = '---\nname: get-artifact\ndescription: Use when Xan asks to see, get, open, receive, deliver, resend, package, or retrieve any generated file/artifact in Telegram or another messaging conversation. Centralizes artifact lookup, verification, packaging, and native MEDIA delivery instead of dumping paths the user cannot inspect.\nversion: 1.0.0\nauthor: Wilson / Hermes Agent\nlicense: MIT\nplatforms: [windows, wsl, linux]\nmetadata:\n  hermes:\n    tags: [artifacts, delivery, telegram, files, media, workspace, verification]\n    related_skills: [task-artifacts-delivery, hermes-agent]\n---\n\n# Get Artifact\n\n## Overview\n\nUse this skill whenever Xan asks for a file/artifact to be sent back in the conversation, or when a task creates durable output that Xan needs to inspect. The failure mode this skill prevents is obvious and stupid: telling him a path exists when Telegram should have received the file as an attachment.\n\nPaths are still useful for auditability. They are not delivery.\n\n## When to Use\n\nUse this skill when Xan says or implies:\n\n- "send it to me as a file"\n- "I can\'t see it"\n- "give me the artifact"\n- "resend the report"\n- "attach the file"\n- "send the patch/summary/state/log"\n- "where is the artifact?" and the practical answer is a file\n- a task generated plans, reports, summaries, scripts, logs, exports, images, audio, video, markdown, JSON, CSV, ZIPs, or any durable output meant for Xan\n\nAlso use this skill after file-patching/config/skill work when a patch summary or ledger entry should be visible to Xan from Telegram.\n\nDo **not** use for:\n\n- ephemeral command output that fits cleanly in the message body\n- secrets, credentials, tokens, private keys, cookies, raw auth dumps\n- destructive moves/deletes unless Xan explicitly approved them\n\n## Core Rule\n\nIf Xan needs to inspect a generated artifact from Telegram, the final response must include a native attachment reference:\n\n```text\nMEDIA:/absolute/path/to/file\n```\n\nA plain Windows path or WSL path is not enough. A Markdown link to a local path is not enough. A promise to send it later is not enough. Attach the file now.\n\n## Delivery Flow\n\n1. **Identify the requested artifact.**\n   - Use the explicit path if Xan gave one.\n   - If he refers to "it", resolve from the last generated/mentioned artifact in the current task.\n   - If ambiguous, search likely locations before asking:\n     - `/mnt/c/Users/santi/Documents/Hermes/Artifacts/`\n     - `/mnt/c/Users/santi/Documents/Hermes/`\n     - `/home/xantastique/.hermes/`\n     - current working directory\n\n2. **Verify before claiming.**\n   - Confirm the file exists.\n   - Confirm nonzero size unless an empty file is expected and explicitly useful.\n   - For generated text artifacts, read a small section if needed to make sure it is the right file.\n\n3. **Make it Telegram-friendly.**\n   - Prefer the original file as the canonical artifact.\n   - For Telegram delivery, create a separate delivery copy when needed:\n     - lowercase ASCII filename\n     - hyphens instead of spaces\n     - short path if possible, e.g. `/tmp/hermes-artifact-test/<task-slug>-summary.md`\n     - preserve the original canonical copy under `Documents/Hermes/Artifacts/...`\n   - If Telegram preview/attachment handling is unreliable for a format, create a copy with a clearer extension or package it:\n     - `.md` -> send directly with a lowercase hyphen slug filename\n     - multiple files -> create a `.zip`\n     - logs with noisy names -> copy to a readable slug filename first\n   - Never rename/move the canonical file just for delivery; copy/package it.\n\n4. **Attach using `MEDIA:`.**\n   - Attach **only the Telegram delivery copy** as `MEDIA:`. Do not also attach the canonical archive copy unless Xan explicitly asks.\n   - For a paired artifact summary, send exactly one PNG and exactly one MP3. Duplicate visual/audio files are noise, not redundancy.\n   - Keep canonical Windows/WSL paths in text for audit/navigation, not as extra `MEDIA:` attachments.\n   - Keep the text short: what it is, why it was sent, and any remaining work.\n   - If a final-response `MEDIA:` attachment does not arrive or is not openable in Telegram, resend the same delivery copy with `send_message(action="send", target="telegram", message="MEDIA:/absolute/path")`. Do not send both canonical and delivery copies.\n\n5. **For multiple deliverables or ZIP bundles, create correlated PNG + audio summaries by default.**\n   - Create a concise PNG image summary named `<task-slug>-summary.png` or `<dream-slug>-summary.png` under the task\'s artifact folder.\n   - Generate a short TTS/audio summary from the same bullet content and name/cache it with the same task/dream slug when possible.\n   - The PNG and audio must be correlated: same scope, same key outcome, same caveat, same remaining work. The audio is the spoken version of the PNG, not a separate ramble.\n   - Use Telegram-safe slug filenames: lowercase ASCII, hyphens, no spaces.\n   - Send the PNG as a native photo via `MEDIA:` and the audio as MP3 via `MEDIA:` so Xan can either look or listen.\n   - Do **not** use `.txt` or `.md` for the primary visible summary unless Xan explicitly asks; those failed in Telegram during testing.\n   - This summary pair is mandatory when sending a ZIP: Xan needs visibility without downloading/opening the archive.\n   - Include what the ZIP contains, why each major file exists, source paths, verification, caveats, and remaining work.\n   - Attach the PNG summary before or alongside the ZIP, and attach the matching audio summary last.\n\n6. **For multiple deliverables, create a manifest when useful.**\n   - Save a concise `Artifact Manifest.md` under the task\'s artifact folder when there are several files or audit details.\n   - Include file names, purpose, source path, verification, and any caveats.\n   - Attach the visible summary plus either all files or a ZIP bundle.\n\n## Packaging Commands\n\nUse tools where possible. When a shell is appropriate:\n\n```bash\n# Verify\nstat -c \'%n %s bytes\' /absolute/path/to/file\n\n# Create a zip bundle from a folder\npython - <<\'PY\'\nfrom pathlib import Path\nfrom zipfile import ZipFile, ZIP_DEFLATED\nsrc = Path(\'/absolute/path/to/folder\')\nout = src.with_suffix(\'.zip\')\nwith ZipFile(out, \'w\', ZIP_DEFLATED) as z:\n    for p in src.rglob(\'*\'):\n        if p.is_file():\n            z.write(p, p.relative_to(src.parent))\nprint(out)\nPY\n```\n\nAvoid `cat`/`head` for reading; use `read_file`. Avoid `ls/find/grep`; use `search_files`.\n\n## Response Shape\n\n```text\nAttached:\n- Visual summary\n  MEDIA:/tmp/hermes-artifact-delivery/task-slug-summary.png\n- Full artifact bundle\n  MEDIA:/tmp/hermes-artifact-delivery/task-slug-bundle.zip\n- Matching audio summary\n  MEDIA:/tmp/hermes-artifact-delivery/task-slug-summary.mp3\n\nCanonical archive paths:\n- PNG: /mnt/c/Users/santi/Documents/Hermes/Artifacts/.../task-slug-summary.png\n- MP3: /mnt/c/Users/santi/Documents/Hermes/Artifacts/.../task-slug-summary.mp3\n\nVerified:\n- PNG summary exists, <size>\n- audio summary exists, <size>\n- bundle exists, <size>\n\nRemaining work:\n- ...\n```\n\nWhen sending a ZIP or large bundle, attach a correlated PNG + audio summary pair by default. Use the same task/dream slug and the same content spine: `<task-slug>-summary.png` plus `<task-slug>-summary.mp3`. Send exactly one copy of each media artifact: the Telegram delivery copy. Do not also attach canonical archive copies; list canonical paths as plain text if useful. The PNG is for visual scanning; the audio is the short spoken version. They should not contradict each other. Strange that this needs saying, but here we are.\n\n## Interaction With STATE.md\n\nFor memory writes, tool-heavy runs, file patches, config edits, skill/plugin changes, or multi-step investigations:\n\n- Append a concise entry to `/mnt/c/Users/santi/Documents/Hermes/STATE.md`.\n- If Xan asks to see it, attach the actual `STATE.md` file via `MEDIA:`.\n- If the entry generated a patch summary or manifest, attach that too.\n\n## Reference Material\n\n- `references/2026-05-24-telegram-artifact-png-audio-pair.md` captures the final Telegram artifact convention: PNG visual summaries plus matching MP3 audio summaries, correlated from the same content spine.\n- `references/2026-05-24-telegram-artifact-visibility-and-naming.md` captures the earlier correction that Telegram artifacts need native `MEDIA:` attachment, clean slug filenames, and sometimes direct `send_message` delivery when final-response attachment delivery is unreliable.\n- `references/2026-05-24-telegram-zip-visible-summary.md` captures the intermediate correction that ZIP bundles must be accompanied by a visible summary artifact for visibility without opening the archive.\n\n## Common Pitfalls\n\n1. **Only giving a path.** Xan may not be at the machine. Telegram needs an attachment.\n2. **Assuming `MEDIA:` happened when it did not.** Put the literal `MEDIA:/absolute/path` in the final response.\n3. **Sending a directory.** Package directories as ZIPs first.\n4. **Attaching stale artifacts.** Verify modification time/content when the request is contextual.\n5. **Leaking secrets.** Redact or refuse to attach credential material unless explicitly safe and intentional.\n6. **Cluttering Desktop.** Use `Documents/Hermes/Artifacts/...`; never dump delivery copies on Desktop.\n7. **Over-speaking in TTS.** Voice summary should say what was attached, not recite paths.\n8. **Letting PNG and audio drift.** For paired summaries, generate both from the same bullet content. If the PNG says one risk and the MP3 says another, you made two little lies instead of one summary.\n\n## Verification Checklist\n\n- [ ] Correct artifact identified\n- [ ] File exists and size checked\n- [ ] If sending a ZIP, correlated PNG + audio summary pair named `<task-slug>-summary.png` and `<task-slug>-summary.mp3` created\n- [ ] Exactly one delivery copy of each media artifact attached as `MEDIA:`; canonical archive paths listed as text only unless Xan asks for duplicate attachments\n- [ ] If multiple files, manifest or ZIP created\n- [ ] Final response includes `MEDIA:/absolute/path/to/file` for summary and bundle/file\n- [ ] Text says what was attached\n- [ ] Remaining work included when relevant\n- [ ] STATE.md updated when the run involved memory/config/skill/tool-heavy changes\n'


class CommandError(RuntimeError):
    pass


@dataclass(frozen=True)
class BootstrapConfig:
    public_key: str
    replace_authorized_keys: bool = False
    install_seed_files: bool = False
    hermes_home: Path | None = None
    dry_run: bool = False


class CommandRunner:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def run(self, command: list[str], check: bool = True) -> subprocess.CompletedProcess | None:
        print('+', ' '.join(command))
        if self.dry_run:
            return None
        return subprocess.run(command, check=check, text=True)


class PlatformGuard:
    @staticmethod
    def is_windows() -> bool:
        return platform.system().lower() == 'windows'

    @staticmethod
    def is_admin() -> bool:
        if not PlatformGuard.is_windows():
            return os.geteuid() == 0 if hasattr(os, 'geteuid') else False
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    @classmethod
    def require_windows_admin(cls) -> None:
        if not cls.is_windows():
            raise CommandError('windows-ssh mode must run on Windows from elevated PowerShell.')
        if not cls.is_admin():
            raise CommandError('Administrator privileges required. Re-run PowerShell as Administrator.')


class FileBackup:
    @staticmethod
    def backup_if_exists(path: Path) -> Path | None:
        if not path.exists():
            return None
        stamp = datetime.now().strftime('%Y%m%d%H%M%S')
        backup_path = path.with_name(f'{path.name}.bak.{stamp}')
        shutil.copy2(path, backup_path)
        print(f'Backed up {path} -> {backup_path}')
        return backup_path


class AuthorizedKeysManager:
    def __init__(self, path: Path) -> None:
        self.path = path

    def write_key(self, public_key: str, replace: bool) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        FileBackup.backup_if_exists(self.path)
        if replace:
            self.path.write_text(public_key.strip() + '\n', encoding='utf-8')
            print(f'Replaced {self.path} with controller key only.')
            return
        self._write_marked_block(public_key)

    def _write_marked_block(self, public_key: str) -> None:
        marker_start = '# BEGIN HERMES CONTROLLER KEY'
        marker_end = '# END HERMES CONTROLLER KEY'
        block = f'{marker_start}\n{public_key.strip()}\n{marker_end}\n'
        existing = self.path.read_text(encoding='utf-8') if self.path.exists() else ''
        if marker_start in existing and marker_end in existing:
            before = existing.split(marker_start)[0]
            after = existing.split(marker_end, 1)[1]
            new_content = before.rstrip() + '\n' + block + after.lstrip()
        else:
            new_content = existing.rstrip() + '\n' + block if existing.strip() else block
        self.path.write_text(new_content, encoding='utf-8')
        print(f'Updated marked controller key block in {self.path}.')


class WindowsAclManager:
    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner

    def harden_user_ssh_acl(self, ssh_dir: Path, authorized_keys: Path) -> None:
        user = os.environ.get('USERNAME') or os.getlogin()
        commands = [
            ['icacls', str(ssh_dir), '/inheritance:r'],
            ['icacls', str(ssh_dir), '/grant', f'{user}:(OI)(CI)F', 'SYSTEM:(OI)(CI)F'],
            ['icacls', str(authorized_keys), '/inheritance:r'],
            ['icacls', str(authorized_keys), '/grant', f'{user}:F', 'SYSTEM:F'],
        ]
        for command in commands:
            self.runner.run(command, check=False)

    def harden_admin_authorized_keys_acl(self, authorized_keys: Path) -> None:
        # Windows OpenSSH uses this file for administrator accounts and is strict about ACLs.
        # Users/Authenticated Users/Everyone permissions make key auth fail silently.
        commands = [
            ['icacls', str(authorized_keys), '/inheritance:r'],
            ['icacls', str(authorized_keys), '/grant', 'Administrators:F', 'SYSTEM:F'],
            ['icacls', str(authorized_keys), '/remove', 'Users', 'Authenticated Users', 'Everyone'],
        ]
        for command in commands:
            self.runner.run(command, check=False)


class SeedInstaller:
    """Installs child-safe seeds only. No init skill is installed on child nodes."""

    def __init__(self, hermes_home: Path) -> None:
        self.hermes_home = hermes_home

    def install(self) -> None:
        self.hermes_home.mkdir(parents=True, exist_ok=True)
        self._write('SOUL.md', SOUL_MD)
        self._write('agent-seed/Xan Preference Seed.md', PREFERENCE_SEED_MD)
        self._write('agent-seed/sync_policy.yaml', SYNC_POLICY_YAML)
        self._write('agent-seed/Agent Message Contract.md', AGENT_CONTRACT_MD)
        self._write('skills/software-development/plan-mode/SKILL.md', PLAN_MODE_SKILL)
        self._write('skills/productivity/get-artifact/SKILL.md', GET_ARTIFACT_SKILL)
        self._copy_bundled_common_skills()
        self._copy_bundled_helpers()
        print(f'Installed child-safe seeds under {self.hermes_home}')
        print('Init skills were intentionally not installed on this child node.')

    def _write(self, relative_path: str, content: str) -> None:
        path = self.hermes_home / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        print(f'Wrote {path}')

    def _copy_bundled_common_skills(self) -> None:
        package_root = Path(__file__).resolve().parents[2]
        bundled = package_root / 'skills' / 'core-common'
        if not bundled.exists():
            return
        category_map = {
            'git-gh': 'software-development',
            'plan-mode': 'software-development',
            'get-artifact': 'productivity',
            'storage-explorer': 'productivity',
            'file-organization': 'productivity',
            'meta-gateway': 'autonomous-ai-agents',
            'orchestration': 'autonomous-ai-agents',
            'omni-qa': 'software-development',
            'image-gen': 'creative',
            'get-movie': 'media',
            'get-show': 'media',
            'get-music': 'media',
            'screenshot': 'productivity',
        }
        for skill_dir in bundled.iterdir():
            skill_md = skill_dir / 'SKILL.md'
            if not skill_md.exists():
                continue
            skill_name = skill_dir.name
            if skill_name in {'plan-mode', 'get-artifact'}:
                continue
            category = category_map.get(skill_name, 'productivity')
            target = self.hermes_home / 'skills' / category / skill_name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(skill_dir, target)
            print(f'Installed bundled common skill {skill_name} -> {target}')
        media_shared = bundled / 'media-shared'
        if media_shared.exists():
            target = self.hermes_home / 'skills' / 'media'
            target.mkdir(parents=True, exist_ok=True)
            for child in media_shared.iterdir():
                dst = target / child.name
                if dst.exists():
                    if dst.is_dir():
                        shutil.rmtree(dst)
                    else:
                        dst.unlink()
                if child.is_dir():
                    shutil.copytree(child, dst)
                else:
                    shutil.copy2(child, dst)
                print(f'Installed bundled media shared component {child.name} -> {dst}')

    def _copy_bundled_helpers(self) -> None:
        package_root = Path(__file__).resolve().parents[2]
        bundled = package_root / 'helpers'
        if not bundled.exists():
            return
        documents = Path.home() / 'Documents'
        target = documents / 'Hermes' / 'helpers'
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(bundled, target)
        print(f'Installed bundled helpers -> {target}')


class WindowsOpenSshBootstrapper:
    def __init__(self, config: BootstrapConfig, runner: CommandRunner) -> None:
        self.config = config
        self.runner = runner

    def run(self) -> None:
        PlatformGuard.require_windows_admin()
        self._install_openssh_server()
        self._start_and_enable_sshd()
        self._ensure_firewall_rule()
        self._configure_authorized_keys()
        if self.config.install_seed_files:
            hermes_home = self.config.hermes_home or (Path.home() / '.hermes')
            SeedInstaller(hermes_home).install()
        self._restart_sshd()
        print('Windows SSH bootstrap complete.')
        print('Verify from controller: ssh <windows-user>@100.76.137.32 hostname')

    def _powershell(self, script: str, check: bool = True) -> None:
        self.runner.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', script], check=check)

    def _install_openssh_server(self) -> None:
        script = "if (-not (Get-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 | ? State -eq 'Installed')) { Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 }"
        self._powershell(script)

    def _start_and_enable_sshd(self) -> None:
        self._powershell('Set-Service -Name sshd -StartupType Automatic; Start-Service sshd', check=False)

    def _ensure_firewall_rule(self) -> None:
        script = "if (-not (Get-NetFirewallRule -Name 'OpenSSH-Server-In-TCP-Tailscale' -ErrorAction SilentlyContinue)) { New-NetFirewallRule -Name 'OpenSSH-Server-In-TCP-Tailscale' -DisplayName 'OpenSSH Server over Tailscale' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 -Profile Private }"
        self._powershell(script, check=False)

    def _configure_authorized_keys(self) -> None:
        # Default to Windows OpenSSH's administrator key path. LilJon's Windows users are
        # administrator-class accounts, so per-user authorized_keys can be ignored by sshd.
        # This was the likely cause of controller key rejection despite port 22 being open.
        admin_authorized_keys = Path(os.environ.get('PROGRAMDATA', r'C:\ProgramData')) / 'ssh' / 'administrators_authorized_keys'
        AuthorizedKeysManager(admin_authorized_keys).write_key(
            self.config.public_key,
            replace=self.config.replace_authorized_keys,
        )
        WindowsAclManager(self.runner).harden_admin_authorized_keys_acl(admin_authorized_keys)
        print(f'Configured Windows administrator authorized keys at {admin_authorized_keys}')

    def _restart_sshd(self) -> None:
        self._powershell('Restart-Service sshd', check=False)


class ControllerUpdateVerifier:
    """Verifies controller-authored update manifests using SSH signatures."""

    def __init__(self, manifest: Path, signature: Path, allowed_signers: Path, identity: str = 'Lazarus', namespace: str = 'hermes-init-update') -> None:
        self.manifest = manifest
        self.signature = signature
        self.allowed_signers = allowed_signers
        self.identity = identity
        self.namespace = namespace

    def run(self) -> None:
        for path in [self.manifest, self.signature, self.allowed_signers]:
            if not path.exists():
                raise CommandError(f'Controller update verification failed: missing {path}')
        command = [
            'ssh-keygen', '-Y', 'verify',
            '-f', str(self.allowed_signers),
            '-I', self.identity,
            '-n', self.namespace,
            '-s', str(self.signature),
        ]
        try:
            cp = subprocess.run(command, input=self.manifest.read_bytes(), capture_output=True, timeout=30)
        except FileNotFoundError as exc:
            raise CommandError('Controller update verification failed: ssh-keygen not found. Stop and ask Xan/Lazarus for manual approval or install OpenSSH.') from exc
        except subprocess.TimeoutExpired as exc:
            raise CommandError('Controller update verification failed: ssh-keygen verification timed out.') from exc
        if cp.returncode != 0:
            stderr = cp.stderr.decode(errors='replace').strip()
            stdout = cp.stdout.decode(errors='replace').strip()
            raise CommandError(f'Controller update verification failed. stdout={stdout!r} stderr={stderr!r}')
        print('Controller update signature verified.')
        print(f'Manifest: {self.manifest}')
        print(f'Allowed signer identity: {self.identity}')
        print(f'Namespace: {self.namespace}')


class WindowsVerifier:
    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner

    def run(self) -> None:
        PlatformGuard.require_windows_admin()
        script = r'''
$ErrorActionPreference = 'Continue'
Write-Host '=== LilJon Windows SSH Verification ==='
Write-Host ('HOSTNAME=' + $env:COMPUTERNAME)
Write-Host ('USER=' + [Security.Principal.WindowsIdentity]::GetCurrent().Name)
$adminKeys = 'C:\ProgramData\ssh\administrators_authorized_keys'
Write-Host ('ADMIN_KEYS_EXISTS=' + (Test-Path $adminKeys))
if (Test-Path $adminKeys) {
  $content = Get-Content -Path $adminKeys -Raw -ErrorAction SilentlyContinue
  Write-Host ('HAS_LAZARUS_ED25519=' + ($content -match 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFN30tVz4lgsj9GViTQK1EoRzYoAemvjWZIQ4sxrL48I'))
  Write-Host 'ADMIN_KEYS_ACL_START'
  icacls $adminKeys
  Write-Host 'ADMIN_KEYS_ACL_END'
}
Get-Service sshd | Select-Object Name,Status,StartType | Format-List
Write-Host 'LOCALHOST_22=' (Test-NetConnection -ComputerName 127.0.0.1 -Port 22 -InformationLevel Quiet)
Write-Host 'LILJON_TAILNET_22=' (Test-NetConnection -ComputerName 100.76.137.32 -Port 22 -InformationLevel Quiet)
Write-Host 'LAZARUS_TAILNET_22=' (Test-NetConnection -ComputerName 100.119.118.63 -Port 22 -InformationLevel Quiet)
$ts = 'C:\Program Files\Tailscale\tailscale.exe'
if (Test-Path $ts) {
  Write-Host 'TAILSCALE_STATUS_START'
  & $ts status
  Write-Host 'TAILSCALE_STATUS_END'
  Write-Host 'TAILSCALE_PING_LAZARUS_START'
  & $ts ping 100.119.118.63
  Write-Host 'TAILSCALE_PING_LAZARUS_END'
} else {
  Write-Host 'TAILSCALE_CLI_MISSING'
}
'''
        self.runner.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', script], check=False)


class InitResultPackager:
    SECRET_NAMES = {'.ssh', '.gnupg', 'AppData', 'Cookies', 'Login Data', 'Local State'}
    TYPE_BUCKETS = {
        'documents': {'.pdf', '.doc', '.docx', '.txt', '.md', '.rtf', '.odt'},
        'spreadsheets': {'.xls', '.xlsx', '.csv', '.tsv', '.ods'},
        'presentations': {'.ppt', '.pptx', '.odp'},
        'images': {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg', '.heic'},
        'video': {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.m4v'},
        'audio': {'.mp3', '.flac', '.wav', '.m4a', '.ogg', '.aac'},
        'archives': {'.zip', '.7z', '.rar', '.tar', '.gz'},
        'code': {'.py', '.js', '.ts', '.tsx', '.jsx', '.ps1', '.sh', '.bat', '.go', '.rs', '.java', '.cs', '.cpp', '.c', '.h', '.json', '.yaml', '.yml', '.toml'},
        'executables': {'.exe', '.msi', '.dll', '.sys'},
    }

    def __init__(self, output: Path) -> None:
        self.output = output
        self.workdir = output.with_suffix('')

    def run(self) -> None:
        self.workdir.mkdir(parents=True, exist_ok=True)
        awareness = self._collect_awareness()
        self._write_registries(awareness)
        (self.workdir / 'situational_awareness.json').write_text(json.dumps(awareness, indent=2, ensure_ascii=False), encoding='utf-8')
        (self.workdir / 'controller_ingest.md').write_text(self._controller_ingest_md(awareness), encoding='utf-8')
        (self.workdir / 'README.md').write_text(self._readme_md(), encoding='utf-8')
        self._write_command_output('windows_verify.txt', ['py', str(Path(__file__).resolve().parents[2] / 'init.py'), 'windows-verify'])
        self._zip_dir(self.workdir, self.output)
        print(f'Wrote init result bundle: {self.output}')
        print('Send this init_res.zip back to Xan/Lazarus for controller-side ingestion.')

    def _collect_awareness(self) -> dict:
        home = Path.home()
        roots = [home, home / 'Documents', home / 'Downloads', home / 'Desktop', home / 'Pictures', home / 'Videos']
        hermes = home / 'Documents' / 'Hermes'
        if hermes.exists():
            roots.append(hermes)
        drive_roots = self._drive_roots()
        roots.extend(drive_roots)
        path_maps = {str(root): self._path_summary(root) for root in roots if root.exists()}
        return {
            'agent': {'name': 'Arby', 'body': 'LilJon', 'hostname_expected': 'desktop-mca3em3'},
            'captured_at': datetime.now().isoformat(timespec='seconds'),
            'machine': self._machine_info(),
            'drives': [self._drive_summary(d) for d in drive_roots],
            'installed_programs': self._installed_programs(),
            'path_maps': path_maps,
            'content_type_totals': self._merge_content_types(path_maps),
            'important_state': self._important_state(),
            'ssh_key_state': self._ssh_key_state(),
            'registries': {
                'agent_registry': 'registries/agent_registry.json',
                'machine_registry': 'registries/machine_registry.json',
                'drive_registry': 'registries/drive_registry.json',
                'path_registry': 'registries/path_registry.json',
                'program_registry': 'registries/program_registry.json',
                'service_registry': 'registries/service_registry.json',
            },
            'controller_import': {
                'suggested_memory_subject': 'Arby/LilJon situational awareness',
                'purpose': 'Give Lazarus an enhanced map of subordinate-only paths, content types, drive layout, and system state.',
                'do_not_import': ['secrets', 'private_keys', 'raw_env', 'browser_profiles'],
                'ssh_material_allowed': ['controller_public_key_status', 'public_key_fingerprint', 'authorized_keys_acl_report'],
            },
        }

    def _machine_info(self) -> dict:
        return {
            'hostname': os.environ.get('COMPUTERNAME') or platform.node(),
            'user': os.environ.get('USERNAME') or os.getlogin(),
            'home': str(Path.home()),
            'platform': platform.platform(),
            'processor': platform.processor(),
        }

    def _drive_roots(self) -> list[Path]:
        roots = []
        for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
            p = Path(f'{letter}:/')
            if p.exists():
                roots.append(p)
        return roots

    def _drive_summary(self, root: Path) -> dict:
        try:
            usage = shutil.disk_usage(root)
            return {'root': str(root), 'total': usage.total, 'used': usage.used, 'free': usage.free}
        except Exception as e:
            return {'root': str(root), 'error': str(e)}

    def _installed_programs(self) -> list[dict]:
        script = r'''
$paths = @(
  'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
  'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
  'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*'
)
$items = foreach ($p in $paths) {
  Get-ItemProperty $p -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName } |
    Select-Object DisplayName,DisplayVersion,Publisher,InstallDate,InstallLocation
}
$items | Sort-Object DisplayName -Unique | ConvertTo-Json -Compress -Depth 3
'''
        raw = self._capture(['powershell', '-NoProfile', '-Command', script], 30)
        try:
            parsed = json.loads(raw) if raw else []
            if isinstance(parsed, dict):
                return [parsed]
            return parsed[:500]
        except Exception:
            return [{'error': 'failed_to_parse_installed_programs', 'raw_excerpt': raw[:2000]}]

    def _path_summary(self, root: Path, max_depth: int = 3, max_files: int = 5000) -> dict:
        summary = {'root': str(root), 'top_level': [], 'counts': {'files': 0, 'dirs': 0, 'bytes': 0}, 'content_types': {}, 'truncated': False}
        try:
            for child in sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))[:80]:
                if child.name in self.SECRET_NAMES:
                    summary['top_level'].append({'name': child.name, 'kind': 'skipped_sensitive'})
                    continue
                try:
                    st = child.stat()
                    summary['top_level'].append({'name': child.name, 'kind': 'dir' if child.is_dir() else 'file', 'bytes': st.st_size})
                except Exception:
                    summary['top_level'].append({'name': child.name, 'kind': 'error'})
        except Exception as e:
            summary['error'] = str(e)
            return summary
        for current, dirs, files in os.walk(root):
            rel_depth = len(Path(current).relative_to(root).parts) if Path(current) != root else 0
            dirs[:] = [d for d in dirs if d not in self.SECRET_NAMES and rel_depth < max_depth]
            summary['counts']['dirs'] += len(dirs)
            for name in files:
                summary['counts']['files'] += 1
                p = Path(current) / name
                bucket = self._bucket(p.suffix.lower())
                entry = summary['content_types'].setdefault(bucket, {'files': 0, 'bytes': 0})
                entry['files'] += 1
                try:
                    size = p.stat().st_size
                except Exception:
                    size = 0
                entry['bytes'] += size
                summary['counts']['bytes'] += size
                if summary['counts']['files'] >= max_files:
                    summary['truncated'] = True
                    return summary
        return summary

    def _bucket(self, ext: str) -> str:
        for bucket, exts in self.TYPE_BUCKETS.items():
            if ext in exts:
                return bucket
        return 'other_or_unknown'

    def _merge_content_types(self, path_maps: dict) -> dict:
        total = {}
        for data in path_maps.values():
            for bucket, entry in data.get('content_types', {}).items():
                t = total.setdefault(bucket, {'files': 0, 'bytes': 0})
                t['files'] += entry.get('files', 0)
                t['bytes'] += entry.get('bytes', 0)
        return total

    def _ssh_key_state(self) -> dict:
        """Report public SSH setup state only. Never include private keys."""
        script = r'''
$adminKeys = 'C:\ProgramData\ssh\administrators_authorized_keys'
$result = [ordered]@{
  admin_authorized_keys_path = $adminKeys
  exists = (Test-Path $adminKeys)
  contains_lazarus_public_key = $false
  controller_public_key_algorithm = 'ssh-ed25519'
  controller_public_key_comment = 'hermes-tailscale-homelan'
  forbidden_private_key_export = $true
  acl = $null
}
if (Test-Path $adminKeys) {
  $content = Get-Content -Path $adminKeys -Raw -ErrorAction SilentlyContinue
  $result.contains_lazarus_public_key = ($content -match 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFN30tVz4lgsj9GViTQK1EoRzYoAemvjWZIQ4sxrL48I')
  $result.acl = (icacls $adminKeys 2>&1 | Out-String).Trim()
}
$result | ConvertTo-Json -Compress -Depth 4
'''
        raw = self._capture(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', script], 20)
        try:
            return json.loads(raw) if raw else {'error': 'empty_ssh_key_state'}
        except Exception:
            return {'error': 'failed_to_parse_ssh_key_state', 'raw_excerpt': raw[:2000]}

    def _important_state(self) -> dict:
        return {
            'sshd_service': self._capture(['powershell', '-NoProfile', '-Command', "Get-Service sshd | Select Name,Status,StartType | ConvertTo-Json -Compress"], 15),
            'tailscale_status': self._capture(['powershell', '-NoProfile', '-Command', "if (Test-Path 'C:\\Program Files\\Tailscale\\tailscale.exe') { & 'C:\\Program Files\\Tailscale\\tailscale.exe' status }"], 20),
            'network_adapters': self._capture(['powershell', '-NoProfile', '-Command', "Get-NetIPConfiguration | Select InterfaceAlias,IPv4Address,IPv6Address | ConvertTo-Json -Compress"], 20),
        }

    def _capture(self, command: list[str], timeout: int) -> str:
        try:
            cp = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            return (cp.stdout + cp.stderr).strip()[:12000]
        except Exception as e:
            return f'ERROR: {e}'

    def _write_command_output(self, name: str, command: list[str]) -> None:
        (self.workdir / name).write_text(self._capture(command, 90), encoding='utf-8')

    def _write_registries(self, awareness: dict) -> None:
        reg = self.workdir / 'registries'
        reg.mkdir(parents=True, exist_ok=True)
        agent_registry = {
            'agent_name': 'Arby',
            'body_name': 'LilJon',
            'role': 'child-agent/laptop',
            'machine_name': awareness.get('machine', {}).get('hostname'),
            'tailscale_ip': '100.76.137.32',
            'controller': {'agent': 'Wilson', 'body': 'Lazarus', 'tailscale_ip': '100.119.118.63'},
            'status': 'initialized-reporting-to-controller',
            'captured_at': awareness.get('captured_at'),
        }
        machine_registry = awareness.get('machine', {}) | {'important_state': awareness.get('important_state', {}), 'ssh_key_state': awareness.get('ssh_key_state', {})}
        drive_registry = {'drives': awareness.get('drives', []), 'captured_at': awareness.get('captured_at')}
        path_registry = {'path_maps': awareness.get('path_maps', {}), 'content_type_totals': awareness.get('content_type_totals', {})}
        program_registry = {'installed_programs': awareness.get('installed_programs', []), 'captured_at': awareness.get('captured_at')}
        service_registry = {'important_state': awareness.get('important_state', {}), 'captured_at': awareness.get('captured_at')}
        for name, data in {
            'agent_registry.json': agent_registry,
            'machine_registry.json': machine_registry,
            'drive_registry.json': drive_registry,
            'path_registry.json': path_registry,
            'program_registry.json': program_registry,
            'service_registry.json': service_registry,
        }.items():
            (reg / name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

    def _controller_ingest_md(self, awareness: dict) -> str:
        return f"""# LilJon init result — controller ingest

## Identity
- Agent: Arby
- Body: LilJon
- Hostname observed: {awareness['machine'].get('hostname')}
- User observed: {awareness['machine'].get('user')}

## Purpose
Import this into Lazarus as subordinate situational awareness, not as blind memory spam.

## Programmatic situational awareness means
- drive roots and free space
- bounded path maps for user/profile/Hermes/drive roots
- content-type distribution by extension bucket
- installed programs registry
- JSON registries for agent, machine, drives, paths, programs, and services
- SSH/Tailscale/service/network state only visible from LilJon
- meta-gateway comms hierarchy/registry state
- public SSH key status/fingerprint and authorized-key ACL state; never private keys

## Controller action
- Review `situational_awareness.json`.
- Save compact durable facts about LilJon/Arby only.
- Do not import secrets, raw env, private keys, browser profiles, or raw memory dumps.
- Use public SSH key status/fingerprints only to finish setup and verification.
"""

    def _readme_md(self) -> str:
        return """# init_res.zip

Return this bundle to Xan/Lazarus after running LilJon init.

Contains:
- `situational_awareness.json` — programmatic local map of LilJon
- `registries/*.json` — agent, machine, drive, path, program, and service registries
- `windows_verify.txt` — LilJon-side SSH/Tailscale verification, public key status, and ACLs
- `controller_ingest.md` — what Lazarus should import/review

This bundle may contain public SSH key status/fingerprints and ACL reports. It must not contain secrets, private keys, raw `.env`, or browser profiles.
"""

    def _zip_dir(self, src: Path, dst: Path) -> None:
        if dst.exists():
            dst.unlink()
        with zipfile.ZipFile(dst, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for path in src.rglob('*'):
                if path.is_file():
                    zf.write(path, path.relative_to(src))


class WslCommandEmitter:
    def __init__(self, config: BootstrapConfig) -> None:
        self.config = config

    def emit(self) -> str:
        auth_write = self._authorized_keys_block()
        return f"""# Run inside laptop WSL
set -euo pipefail
sudo apt update
sudo apt install -y openssh-server
sudo mkdir -p /run/sshd
mkdir -p ~/.ssh
chmod 700 ~/.ssh
if [ -f ~/.ssh/authorized_keys ]; then cp ~/.ssh/authorized_keys ~/.ssh/authorized_keys.bak.$(date +%Y%m%d%H%M%S); fi
{auth_write}
chmod 600 ~/.ssh/authorized_keys
sudo mkdir -p /etc/ssh/sshd_config.d
printf 'Port 2222\nPasswordAuthentication no\nPubkeyAuthentication yes\n' | sudo tee /etc/ssh/sshd_config.d/99-hermes-agent.conf >/dev/null
sudo service ssh restart || sudo systemctl restart ssh || sudo /usr/sbin/sshd
mkdir -p ~/.hermes/skills/software-development/plan-mode ~/.hermes/skills/productivity/get-artifact ~/.hermes/agent-seed
cat > ~/.hermes/SOUL.md <<'EOF_SOUL'
{SOUL_MD}
EOF_SOUL
cat > ~/.hermes/agent-seed/'Xan Preference Seed.md' <<'EOF_PREF'
{PREFERENCE_SEED_MD}
EOF_PREF
cat > ~/.hermes/agent-seed/sync_policy.yaml <<'EOF_SYNC'
{SYNC_POLICY_YAML}
EOF_SYNC
cat > ~/.hermes/agent-seed/'Agent Message Contract.md' <<'EOF_CONTRACT'
{AGENT_CONTRACT_MD}
EOF_CONTRACT
cat > ~/.hermes/skills/software-development/plan-mode/SKILL.md <<'EOF_PLAN'
{PLAN_MODE_SKILL}
EOF_PLAN
cat > ~/.hermes/skills/productivity/get-artifact/SKILL.md <<'EOF_ARTIFACT'
{GET_ARTIFACT_SKILL}
EOF_ARTIFACT
if [ -d ./skills/core-common ]; then
  for skill in ./skills/core-common/*; do
    [ -d "$skill" ] || continue
    name="$(basename "$skill")"
    [ -f "$skill/SKILL.md" ] || continue
    case "$name" in
      git-gh|plan-mode|omni-qa) category="software-development" ;;
      get-artifact|storage-explorer|file-organization|screenshot) category="productivity" ;;
      meta-gateway|orchestration) category="autonomous-ai-agents" ;;
      image-gen) category="creative" ;;
      get-movie|get-show|get-music) category="media" ;;
      *) category="productivity" ;;
    esac
    if [ "$name" = "plan-mode" ] || [ "$name" = "get-artifact" ]; then continue; fi
    mkdir -p "$HOME/.hermes/skills/$category"
    rm -rf "$HOME/.hermes/skills/$category/$name"
    cp -R "$skill" "$HOME/.hermes/skills/$category/$name"
  done
  if [ -d ./skills/core-common/media-shared ]; then
    mkdir -p "$HOME/.hermes/skills/media"
    cp -R ./skills/core-common/media-shared/* "$HOME/.hermes/skills/media/"
  fi
  if [ -d ./helpers ]; then
    mkdir -p "$HOME/Documents/Hermes"
    rm -rf "$HOME/Documents/Hermes/helpers"
    cp -R ./helpers "$HOME/Documents/Hermes/helpers"
    printf 'Installed bundled helpers into ~/Documents/Hermes/helpers.\n'
  fi
else
  printf 'Bundled common skills not found in current directory; extracted init package skills were not copied.\n'
fi
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
hermes doctor || true
printf '\nChild seed complete. Init authority was not installed on this node.\n'
"""

    def _authorized_keys_block(self) -> str:
        key = self.config.public_key.strip()
        if self.config.replace_authorized_keys:
            return "cat > ~/.ssh/authorized_keys <<'EOF_KEY'\n" + key + "\nEOF_KEY"
        escaped = key.replace("'", "'\\''")
        return f"grep -qxF '{escaped}' ~/.ssh/authorized_keys || printf '%s\\n' '{escaped}' >> ~/.ssh/authorized_keys"


class Cli:
    def __init__(self) -> None:
        self.parser = self._build_parser()

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description='Initialize a child Hermes node without installing init authority on it.')
        sub = parser.add_subparsers(dest='cmd', required=True)

        win = sub.add_parser('windows-ssh', help='Configure Windows OpenSSH on this laptop.')
        self._add_common_args(win)
        win.add_argument('--install-seed-files', action='store_true', help='Install child-safe SOUL/preferences/common skills.')
        win.add_argument('--hermes-home', type=Path, default=None)
        win.add_argument('--dry-run', action='store_true')

        verify = sub.add_parser('windows-verify', help='Verify LilJon SSH/Tailscale readiness from the laptop side.')
        verify.add_argument('--dry-run', action='store_true')

        res = sub.add_parser('make-init-res', help='Create init_res.zip for return to Xan/Lazarus.')
        res.add_argument('--output', type=Path, default=Path('init_res.zip'))
        res.add_argument('--dry-run', action='store_true')

        wsl = sub.add_parser('print-wsl-commands', help='Print commands to run inside laptop WSL.')
        self._add_common_args(wsl)

        upd = sub.add_parser('verify-controller-update', help='Verify a controller-authored init update manifest signature.')
        upd.add_argument('--manifest', type=Path, default=Path('controller_update.json'))
        upd.add_argument('--signature', type=Path, default=Path('controller_update.sig'))
        upd.add_argument('--allowed-signers', type=Path, default=Path('controllers/lazarus_allowed_signers'))
        upd.add_argument('--identity', default='Lazarus')
        upd.add_argument('--namespace', default='hermes-init-update')

        return parser

    @staticmethod
    def _add_common_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--public-key', default=DEFAULT_PUBLIC_KEY)
        parser.add_argument('--replace-authorized-keys', action='store_true', help='Replace authorized_keys with controller key only after backup.')

    def run(self) -> None:
        args = self.parser.parse_args()
        config = BootstrapConfig(
            public_key=getattr(args, 'public_key', DEFAULT_PUBLIC_KEY),
            replace_authorized_keys=getattr(args, 'replace_authorized_keys', False),
            install_seed_files=getattr(args, 'install_seed_files', False),
            hermes_home=getattr(args, 'hermes_home', None),
            dry_run=getattr(args, 'dry_run', False),
        )
        if args.cmd == 'windows-ssh':
            WindowsOpenSshBootstrapper(config, CommandRunner(config.dry_run)).run()
        elif args.cmd == 'windows-verify':
            WindowsVerifier(CommandRunner(config.dry_run)).run()
        elif args.cmd == 'make-init-res':
            InitResultPackager(getattr(args, 'output', Path('init_res.zip'))).run()
        elif args.cmd == 'print-wsl-commands':
            print(WslCommandEmitter(config).emit())
        elif args.cmd == 'verify-controller-update':
            ControllerUpdateVerifier(args.manifest, args.signature, args.allowed_signers, args.identity, args.namespace).run()
        else:
            raise CommandError(f'Unknown command: {args.cmd}')


