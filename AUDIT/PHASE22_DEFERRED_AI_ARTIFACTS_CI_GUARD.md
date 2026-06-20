# Phase 22 Deferred AI Artifacts CI Guard

Status: DRAFT FOR AUDIT REVIEW
Phase: 22.6
Scope: CI guard for deferred AI artifacts and deferred AI tools
Source Of Truth: Repository files only
Production Release: BLOCKED WITHOUT APPROVAL
Destructive Automation: BLOCKED
Secrets Handling: DO NOT STORE OR PRINT SECRETS

## Purpose

This artifact documents a repository guard that fails if raw or deferred AI artifacts are committed. The guard inspects tracked files only, so local untracked deferred files remain preserved and do not fail validation.

## Guarded Paths

The guard fails if any tracked file is under or exactly matches:

```text
AI_AUDIT/
tools/ai/bridge_claude.py
tools/ai/bridge_claude_repo.py
tools/ai/s43_supervisor.py
```

## Tool

```text
tools/ai/check_no_deferred_ai_artifacts.py
```

The tool runs `git ls-files` and checks only tracked paths. It does not read deferred file contents, does not delete files, does not stage files, and does not modify repository state.

## Workflow

```text
.github/workflows/deferred-ai-artifacts-guard.yml
```

The workflow runs on pull requests and pushes to `main`:

```text
python tools/ai/check_no_deferred_ai_artifacts.py
```

## Expected Local Result

The local guard should pass while deferred files remain untracked. It should fail only if a forbidden path becomes tracked.

## Deferred Files Policy

Raw `AI_AUDIT/` evidence and deferred AI bridge/supervisor tools remain local and untracked unless a future approval gate explicitly changes their disposition. Commit-ready evidence must be represented through sanitized `AUDIT/` summaries.

## Validation

Validation for this phase includes:

- Run `python tools/ai/check_no_deferred_ai_artifacts.py`.
- Confirm the command passes with existing untracked deferred files.
- Parse `AUDIT/ROADMAP_CURRENT.json`.
- Confirm no deferred paths are staged or committed.

## Final Rule

The CI guard protects the repository from accidental commitment of raw AI evidence and deferred network-capable AI tools.
