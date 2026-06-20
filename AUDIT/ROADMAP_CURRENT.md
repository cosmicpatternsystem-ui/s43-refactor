# Current Living Roadmap

Status: ACTIVE
Roadmap Version: 2026-06-20.phase22.6
Source Of Truth: Repository files only
Current Phase: 22.6
Current Focus: Deferred AI Artifacts CI Guard
Production Release: BLOCKED WITHOUT APPROVAL
Destructive Automation: BLOCKED
Secrets Handling: DO NOT STORE OR PRINT SECRETS

## Purpose

This file is the mandatory living roadmap for autonomous repository work. It replaces chat memory as the operational source of truth. Agents and operators must read this file and `AUDIT/ROADMAP_CURRENT.json` before proposing or executing roadmap-dependent work.

## Current Authorized Scope

Phase 22.6 authorizes only non-destructive, repository-local, sync-aware deferred artifact guard work:

1. Maintain this living roadmap in markdown and JSON form.
2. Verify roadmap files exist before autonomous cycles proceed.
3. Write local state snapshots under `AI_AUDIT/current_state_snapshot.json` when explicitly invoked.
4. Append timestamped roadmap event JSON files under `AI_AUDIT/roadmap_events/` when explicitly invoked.
5. Validate Python syntax with no-artifact AST parsing.
6. Preserve deferred raw AI outputs and deferred bridge/supervisor scripts.
7. Generate sanitized AI audit summaries under `AUDIT/` without committing raw `AI_AUDIT/` artifacts.
8. Define approval requirements before deferred AI bridge or supervisor tools can be committed or executed.
9. Maintain a commit-safe manifest of deferred files using sanitized metadata only.
10. Enforce a tracked-file CI guard that fails if raw deferred AI artifacts or deferred AI tools are committed.

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
tools/ai/generate_sanitized_audit_evidence.py
AUDIT/AI_AUDIT_SANITIZED_SUMMARY.md
AUDIT/AI_AUDIT_SANITIZED_SUMMARY.json
AUDIT/PHASE22_DEFERRED_AI_TOOL_APPROVAL_GATE.md
AUDIT/PHASE22_DEFERRED_FILES_MANIFEST.md
AUDIT/PHASE22_DEFERRED_AI_ARTIFACTS_CI_GUARD.md
tools/ai/check_no_deferred_ai_artifacts.py
.github/workflows/deferred-ai-artifacts-guard.yml
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
8. Sanitized AI audit evidence generator exists and emits only commit-safe summary fields.
9. Sanitized summaries pass leak checks for local paths, raw prompts, raw responses, token metadata, API material, metadata URLs, and unsafe command examples.
10. Deferred AI tool approval gate exists and defines network, secret, redaction, artifact-writing, and pre-commit approval requirements.
11. Deferred files manifest exists and records only sanitized metadata: file identifier, disposition, reason category, approval gate, and commit policy.
12. Deferred AI artifacts CI guard fails if forbidden deferred paths are tracked and passes when deferred files remain untracked.

## Next Action

Review the deferred AI artifacts CI guard, then decide whether to harden bridge/supervisor tools or enforce sanitized evidence generation in automation.

## Phase 22.3 Status

- Objective: Sanitized AI Audit Evidence Generator.
- Generator path: `tools/ai/generate_sanitized_audit_evidence.py`.
- Generated summaries: `AUDIT/AI_AUDIT_SANITIZED_SUMMARY.md`, `AUDIT/AI_AUDIT_SANITIZED_SUMMARY.json`.
- Validation status: AST validation passed; generated summaries passed leak checks.
- Sync status: `main...origin/main` is `0 0`.
- Deferred files: `AI_AUDIT/` and deferred bridge/supervisor scripts remain untracked and preserved.

## Phase 22.6 Status

- Objective: Deferred AI Artifacts CI Guard.
- Guard path: `tools/ai/check_no_deferred_ai_artifacts.py`.
- Workflow path: `.github/workflows/deferred-ai-artifacts-guard.yml`.
- Audit note: `AUDIT/PHASE22_DEFERRED_AI_ARTIFACTS_CI_GUARD.md`.
- Validation target: guard inspects tracked files only using `git ls-files`.
- Sync status: `main...origin/main` is `0 0`.
- Deferred files: `AI_AUDIT/` and deferred bridge/supervisor scripts remain untracked and preserved.

## Phase 22.5 Status

- Objective: Sanitized Deferred Files Manifest.
- Manifest path: `AUDIT/PHASE22_DEFERRED_FILES_MANIFEST.md`.
- Validation target: commit-safe documentation only; raw deferred file contents remain unread and uncommitted.
- Sync status: `main...origin/main` is `0 0`.
- Deferred files: `AI_AUDIT/` and deferred bridge/supervisor scripts remain untracked and preserved.

## Phase 22.4 Status

- Objective: Deferred AI Tool Approval Gate.
- Policy path: `AUDIT/PHASE22_DEFERRED_AI_TOOL_APPROVAL_GATE.md`.
- Validation target: commit-safe documentation only; deferred bridge/supervisor tools remain untouched.
- Sync status: `main...origin/main` is `0 0`.
- Deferred files: `AI_AUDIT/` and deferred bridge/supervisor scripts remain untracked and preserved.
