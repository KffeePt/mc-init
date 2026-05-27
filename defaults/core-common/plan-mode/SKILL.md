---
name: plan-mode
description: Use when Xan says plan mode, plan for this, make a plan, or asks to plan before execution. Produce a concrete plan and do not implement unless explicitly approved afterward.
version: 1.0.0
author: Wilson / Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, plan-mode, no-exec, workflow, approval]
    related_skills: [plan, writing-plans]
---

# Plan Mode Trigger

## Overview

Use this skill when Xan explicitly asks for plan mode or asks to plan a task before execution. The goal is to separate thinking from doing: inspect only what is needed, write a useful plan, and stop before mutating the target system.

This is a user-local trigger/behavior wrapper around the built-in `plan` skill. If both apply, load `plan` too and follow its save-to-plan-file behavior.

## Trigger Phrases

Load this skill when Xan says any close variant of:

- `plan mode`
- `plan for this`
- `make a plan`
- `write a plan`
- `before doing anything, plan`
- `don't go on yet`
- `do not execute yet`
- `what's the plan`

## Core Behavior

For the current turn:

1. Do not implement the proposed system changes.
2. Do not run mutating commands against the target environment.
3. Do not install software, enable services, open firewall rules, write credentials, or start daemons unless Xan explicitly exits plan mode and approves execution.
4. Read-only inspection is allowed when it materially improves the plan.
5. If the plan itself should be durable, save a markdown plan under `.hermes/plans/` or the shared Hermes artifact workspace, depending on context.
6. End with explicit `Approval needed:` / `Next:` so Xan can say go.

## Plan Shape

Prefer:

```md
## Goal

## Current Facts

## Proposed Architecture

## Step-by-Step Plan

## Commands Xan Runs Manually

## Files/Scripts To Create Later

## Verification

## Risks / Decisions

## Approval Needed
```

For infrastructure/security plans, include:

- trust boundary
- credentials/key handling
- rollback path
- what is not exposed to the public internet
- how to verify from both ends

## Common Pitfalls

1. **Accidental execution.** If Xan says `plan mode`, do not sneak in setup commands just because they look safe.
2. **Omitting exact commands.** A plan can include commands for Xan to run manually. Label them as manual commands, not executed actions.
3. **Blending design and approval.** Stop after the plan. Execution requires a fresh explicit go-ahead.
4. **Security theater.** For remote access plans, prefer standard protocols like SSH over custom connector crypto.

## Verification Checklist

- [ ] No target system mutations were performed.
- [ ] Plan includes exact manual commands or clearly says they will be generated later.
- [ ] Security risks and rollback path are stated.
- [ ] Final response says what approval is needed before execution.
