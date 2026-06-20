# Current Living Roadmap

Status: ACTIVE
Roadmap Version: 2026-06-20.phase22
Source Of Truth: Repository files only
Current Phase: 22
Current Focus: Persistent autonomous control plane and mandatory living roadmap
Production Release: BLOCKED WITHOUT APPROVAL
Destructive Automation: BLOCKED
Secrets Handling: DO NOT STORE OR PRINT SECRETS

## Purpose

This file is the mandatory living roadmap for autonomous repository work. It replaces chat memory as the operational source of truth. Agents and operators must read this file and `AUDIT/ROADMAP_CURRENT.json` before proposing or executing roadmap-dependent work.

## Current Authorized Scope

Phase 22 authorizes only non-destructive, repository-local, sync-aware control-plane work:

1. Maintain this living roadmap in markdown and JSON form.
2. Verify roadmap files exist before autonomous cycles proceed.
3. Write local state snapshots under `AI_AUDIT/current_state_snapshot.json` when explicitly invoked.
4. Append timestamped roadmap event JSON files under `AI_AUDIT/roadmap_events/` when explicitly invoked.
5. Validate Python syntax with no-artifact AST parsing.
6. Preserve deferred raw AI outputs and deferred bridge/supervisor scripts.

## Mandatory Guardrails

- Do not use chat memory as source of truth.
- Do not stage, commit, push, reset, clean, delete branches, or force push without explicit approval.
- Do not execute network-calling AI bridge tools without an approval model.
- Do not commit raw provider prompt/response artifacts.
- Do not create `__pycache__` or `*.pyc` during validation.
- Do not modify deferred files unless a task explicitly scopes them.
- Stop if local `main` is not synchronized with `origin/main`, unless an approved branch workflow is active.

## Deferred Files

The following remain intentionally deferred:

```text
AI_AUDIT/
tools/ai/bridge_claude.py
tools/ai/bridge_claude_repo.py
tools/ai/s43_supervisor.py
```

Deferred means preserved, not deleted, not staged, and not treated as authoritative roadmap state.

## Phase 22 Required Artifacts

```text
AUDIT/ROADMAP_CURRENT.md
AUDIT/ROADMAP_CURRENT.json
AUDIT/PHASE22_PERSISTENT_AUTONOMOUS_CONTROL_PLANE.md
tools/ai/state_journal.py
tools/ai/roadmap_guard.py
tools/ai/write_state_snapshot.py
```

## Phase 22 Exit Criteria

Phase 22 is ready for review when:

1. Roadmap markdown and JSON exist and agree on current phase.
2. `roadmap_guard.py` fails when roadmap files are missing and passes when they exist.
3. `write_state_snapshot.py` writes current repository state to `AI_AUDIT/current_state_snapshot.json` only when invoked.
4. `state_journal.py` appends timestamped event JSON files under `AI_AUDIT/roadmap_events/` only when invoked.
5. AST validation passes without cache artifacts.
6. Deferred files remain preserved and untracked unless separately approved.
7. `main` remains synchronized with `origin/main` unless an approved branch has been created.

## Next Action

Review Phase 22 control-plane artifacts, then request explicit approval before staging or committing candidate files.
