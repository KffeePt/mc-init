# Default Skill Roadmap

Last updated: 2026-05-28
Owner: Wilson / Lazarus
Repo: mc-init

## Current Default Skills (v1.1)

| # | Skill | Status | Version | Category |
|---|---|---|---|---|
| 1 | `plan-mode` | Stable | 1.0.0 | Workflow |
| 2 | `get-artifact` | Stable | 1.0.0 | Delivery |
| 3 | `storage-explorer` | Stable | 2.2.0 | Storage |
| 4 | `file-organization` | Stable | 1.0.0 | Organization |
| 5 | `image-gen` | Stable | 1.0.0 | Creative |
| 6 | `git-gh` | New | 1.0.0 | Version Control |
| 7 | `meta-gateway` | Stable | 1.0.0 | Multi-Agent |
| 8 | `omni-qa` | Stable | 1.0.0 | Quality |
| 9 | `orchestration` | Stable | 1.0.0 | Multi-Agent |
| 10 | `get-movie` | Stable | 1.0.0 | Media |
| 11 | `get-show` | Stable | 1.0.0 | Media |
| 12 | `get-music` | Stable | 1.0.0 | Media |

## Roadmap

### Q3 2026 (Next)

| Skill | Priority | Rationale |
|---|---|---|
| `tailscale-homelan` | High | Child agents need Tailscale awareness for comms verification |
| `personal-server-status-report` | Medium | Unified health reporting across all agents |
| `personal-server-safety-audit` | Low | Security audits need to be child-aware, not only controller-side |

### Q4 2026 (Later)

| Skill | Priority | Rationale |
|---|---|---|
| `obsidian` | Medium | Shared vault management for cross-agent knowledge |
| `huggingface-hub` | Low | ML model access from child agents with GPU |

### Backlog (Deferred)

| Skill | Rationale |
|---|---|
| `kanban-orchestrator` | Too complex for child agents; controller-only |
| `subagent-driven-development` | Requires orchestration that children shouldn't own |
| `test-driven-development` | Dev-only; child agents are ops-first |
| `systematic-debugging` | Good utility but low child-agent relevance |
| `comfyui` | Requires GPU; not all child agents have one |

## Criteria for Default Inclusion

A skill should be a default only if:
1. **Child-safe**: No destructive operations without explicit approval
2. **Self-contained**: Works with minimal external dependencies
3. **Operationally useful**: Relevant to child-agent tasks (observation, reporting, verification)
4. **No init authority**: Does not enable bootstrap or controller-level operations
5. **No secrets exposure**: Does not handle or require credential access

## Skill Categories

| Category | Controller Only | Child Default |
|---|---|---|
| **core-common** | No | Yes — auto-included |
| **comms** | No | Yes — auto-included |
| **init** | Yes — NEVER sent to children | No |
| **local-adapted** | After review | After promotion |
| **private** | Never synced | Never synced |

## Change Log

| Date | Change | Author |
|---|---|---|
| 2026-05-28 | Added media acquisition defaults: `get-movie`, `get-show`, `get-music`; included shared media library in init package | Wilson |
| 2026-05-27 | Initial roadmap; added `git-gh` as default | Wilson |
| 2026-05-26 | Upgraded `storage-explorer` to v2.2.0 (omni-utility) | Wilson |
| 2026-05-25 | Added `file-organization`, `omni-qa`, `orchestration` as defaults | Wilson |


## Drawer Remote State Protocol

- `drawer` repo: `git@github.com:KffeePt/drawer.git`.
- `main` is controller-only.
- Subordinates use `drawer/<group>/<agent-name>-<computer-label>`.
- Git drawer is fallback async comms/state when direct SSH/Tailscale/Hermes gateway is unavailable.
- Conflicts stall scheduled sync, write `.drawer/conflict.json`, and notify Xan/controller instead of auto-resolving.
- `sb-init` is the subordinate-safe init skill; `mc-init` remains controller-only.
