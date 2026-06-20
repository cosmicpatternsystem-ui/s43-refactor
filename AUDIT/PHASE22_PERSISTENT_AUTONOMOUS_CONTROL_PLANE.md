# Phase 22 Persistent Autonomous Control Plane

Status: DRAFT FOR AUDIT REVIEW
Phase: 22
Scope: Repository-local control plane and mandatory living roadmap
Production Release: BLOCKED WITHOUT APPROVAL
Destructive Automation: BLOCKED
Secrets Handling: DO NOT STORE OR PRINT SECRETS

## Purpose

Phase 22 establishes a persistent, repository-local control plane for autonomous work. The control plane makes the repository, not chat memory, the source of operational truth. It provides a living roadmap, a roadmap guard, a state snapshot writer, and a timestamped event journal.

## Control-Plane Principles

1. Repository files are the source of truth.
2. Chat memory is advisory context only and must not be used as durable state.
3. Automation must be non-destructive by default.
4. Sync state must be checked before roadmap-dependent work.
5. Local state snapshots and roadmap events are explicit write actions.
6. Raw AI provider prompts, responses, and bridge outputs remain deferred unless sanitized.
7. Validation must not create bytecode, cache directories, or other artifacts.
8. Staging, committing, pushing, branch deletion, reset, clean, and force-push require separate approval.

## Living Roadmap

The living roadmap consists of:

```text
AUDIT/ROADMAP_CURRENT.md
AUDIT/ROADMAP_CURRENT.json
```

The markdown file is the human-readable roadmap. The JSON file is the machine-readable roadmap. Both must exist before supervised autonomous cycles proceed.

## Roadmap Guard

`tools/ai/roadmap_guard.py` verifies the roadmap files exist and contain the required top-level JSON fields. It fails closed if roadmap files are missing or invalid. It does not write files.

Minimum checks:

- `AUDIT/ROADMAP_CURRENT.md` exists.
- `AUDIT/ROADMAP_CURRENT.json` exists.
- JSON contains `schema_version`, `current_phase`, `current_focus`, `required_artifacts`, and `blocked_actions`.
- Required artifacts are listed.

## State Snapshot Writer

`tools/ai/write_state_snapshot.py` writes current repository state to:

```text
AI_AUDIT/current_state_snapshot.json
```

The snapshot is local evidence only. It must not include secrets or file contents. It records path, branch, commit, upstream, ahead/behind counts, status lines, deferred paths, and roadmap metadata.

## Roadmap Event Journal

`tools/ai/state_journal.py` appends timestamped event JSON files under:

```text
AI_AUDIT/roadmap_events/
```

Events are local audit records. They should describe operator-approved transitions, guard results, validation outcomes, and stop conditions. They must not include secrets or raw provider responses.

## Validation Standard

Syntax validation uses `ast.parse` over source text. `py_compile` is not used for clean validation because it can create `__pycache__` or `*.pyc` files. Any validation that writes cache artifacts is not considered read-only.

## Deferred Files

The following are preserved but excluded from Phase 22 candidate commits unless separately approved:

```text
AI_AUDIT/
tools/ai/bridge_claude.py
tools/ai/bridge_claude_repo.py
tools/ai/s43_supervisor.py
```

## Stop Conditions

Stop before staging or committing if:

1. Roadmap files are missing.
2. `main` is not synchronized with `origin/main` and no approved branch workflow exists.
3. Deferred raw AI outputs would be included.
4. Network-calling tools are required but no approval model exists.
5. Validation creates cache artifacts.
6. Any command would delete, reset, clean, force-push, or mutate secrets.

## Phase 22 Candidate Files

```text
AUDIT/ROADMAP_CURRENT.md
AUDIT/ROADMAP_CURRENT.json
AUDIT/PHASE22_PERSISTENT_AUTONOMOUS_CONTROL_PLANE.md
tools/ai/state_journal.py
tools/ai/roadmap_guard.py
tools/ai/write_state_snapshot.py
```

## Final Rule

A persistent autonomous control plane may observe, guard, journal, and snapshot. It may not approve itself, mutate repository history, push, delete, or treat chat memory as durable state.
