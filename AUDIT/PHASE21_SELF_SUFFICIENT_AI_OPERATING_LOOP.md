# Phase 21 Self-Sufficient AI Operating Loop

Status: DRAFT FOR AUDIT REVIEW
Phase: 21
Scope: Repo-local, audit-focused, non-destructive, sync-aware, approval-gated AI operating loop
Production Release: BLOCKED WITHOUT APPROVAL
Destructive Automation: BLOCKED
Secrets Handling: DO NOT STORE OR PRINT SECRETS

## Purpose

This artifact defines a self-sufficient AI operating loop that reduces manual copy and paste while preserving human approval, repository safety, synchronization awareness, and auditability. The loop is designed for local repository supervision only. It does not authorize commits, pushes, releases, deployments, destructive commands, secret handling, or production financial actions.

## Current Problem

The current workflow still depends on manual prompts, copied command output, and human approvals for each operational step. That model is safe, but it is slow and easy to make inconsistent. Phase 21 moves toward a repo-local loop where deterministic scripts collect evidence, run safety checks, and produce pass/fail reports before a human decides whether to stage, commit, push, or proceed.

## Operating Loop Objective

The target loop is:

1. Inspect repository state.
2. Verify branch, upstream, working tree, and divergence risk.
3. Inventory Phase 21 artifacts and AI audit outputs.
4. Detect risky files before commit review.
5. Run optional dry-run validators.
6. Produce a final pass/fail report.
7. Stop before any action requiring approval.

## Autonomy Levels

### Level 0: Manual Copy/Paste

Operators manually run commands, copy output into prompts, and decide the next action. AI may draft text but has no execution role.

Allowed now: yes.

### Level 1: Read-Only Local Supervisor

Scripts inspect repository state and print audit-friendly reports. They may run read-only git commands, list files, inspect file metadata, and run syntax checks that do not alter source files.

Allowed now: yes.

### Level 2: Local Dry-Run Orchestrator

A local orchestrator runs approved read-only validators in sequence, aggregates results, and exits non-zero when safety checks fail. It may allow documented dry-run exceptions such as an intentionally dirty tree containing Phase 21 artifacts.

Allowed now: yes, for non-destructive dry-run use only.

### Level 3: Approval-Gated Local Writer

Automation may create or update approved local audit artifacts after explicit human approval. It still may not stage, commit, push, delete, deploy, or mutate secrets.

Allowed now: limited. This is allowed only when a user explicitly requests artifact creation within the Phase 21 scope.

### Level 4: Approval-Gated Repository Mutator

Automation may run `git add`, `git commit`, create branches, open pull requests, or push only after explicit approval and clean preflight evidence.

Allowed now: no. This level is out of scope for the current Phase 21 loop.

### Level 5: Approval-Gated Release Operator

Automation may execute release, deployment, rollback, or production-adjacent workflows after full governance, CI, security, rollback, observability, and incident-response evidence.

Allowed now: no.

### Level 6: Fully Autonomous Financial Operator

Automation independently approves and executes production, release, financial, or compliance-impacting actions.

Allowed now: no. This level is not authorized by this repository governance model.

## Allowed Current Capability

The current Phase 21 loop may:

- Inspect repository metadata.
- Inspect file names, sizes, and paths.
- Run `tools/ai/verify_repo_sync.py`.
- Run `tools/ai/precommit_inventory.py`.
- List Phase 21 files and AI audit outputs.
- Run no-artifact Python syntax checks using source reads and `ast.parse`.
- Report pass/fail status.
- Exit non-zero when unsafe conditions are detected.

## Forbidden Current Capability

The current Phase 21 loop must not:

- Run `git add`, `git commit`, `git push`, `git pull`, `git reset`, `git checkout`, `git switch`, `git clean`, or branch/tag mutation.
- Remove files or directories.
- Publish releases or packages.
- Deploy or migrate systems.
- Access, print, request, rotate, or store secrets.
- Modify branch protection, CI policy, environments, or access controls.
- Execute financial transactions or ledger mutations.

## Approval Gates

### Local Artifact Gate

Required before creating or updating audit files or local scripts.

Evidence:

- Requested paths.
- Non-destructive scope.
- Existing files inspected before edit.
- Final status output.

### Commit Gate

Required before staging or committing.

Evidence:

- Sync verifier result.
- Precommit inventory result.
- Exact intended commit files.
- Exact excluded files.
- Human review confirmation.

### Push Gate

Required before remote mutation.

Evidence:

- Clean working tree after commit.
- Upstream state verified.
- Human approval to push.
- Remote target confirmed.

### Release Gate

Required before any release or production action.

Evidence:

- Passing CI.
- Security baseline.
- Rollback plan.
- Observability plan.
- Incident owner.
- Final go/no-go approval.

## Loop Inputs

The loop reads:

- Git metadata.
- `AUDIT/PHASE21_*.md` inventory.
- `AI_AUDIT/` advisory outputs.
- `tools/ai/` local supervisor tooling.
- File path and size metadata for suspicious artifact detection.

The loop must not read or print secret values. If a suspicious secret-like file exists, report the path and stop for human review.

## Loop Outputs

The loop prints:

- Repository sync status.
- Precommit inventory result.
- Phase 21 artifact inventory.
- Optional dry-run validation result.
- Final pass/fail result.
- Blocking conditions and warnings.

The loop does not create, modify, delete, stage, commit, or push files.

## No-Artifact Syntax Validation

Syntax validation must be read-only and must not create cache files, bytecode, or local artifacts. Phase 21 validation uses Python source reads and `ast.parse` so that no `__pycache__` directory or `*.pyc` file is generated.

`py_compile` is disallowed for clean read-only validation because it can create bytecode cache artifacts. It may be considered only when output is redirected to an approved temporary location and cleanup is handled under an explicit policy and human approval.

## Failure Semantics

The loop fails closed when:

1. Repository sync verification fails outside documented dry-run allowance.
2. Suspicious precommit inventory findings exist.
3. Expected Phase 21 files are missing.
4. Python validation fails.
5. A blocked command is requested by policy.
6. Tool output is ambiguous or incomplete.

## Phase 21 Tooling Map

- `tools/ai/safety_policy.py`: Defines allowed read-only commands, blocked commands, and approval-required commands.
- `tools/ai/precommit_inventory.py`: Reports suspicious local files before human commit review.
- `tools/ai/verify_repo_sync.py`: Verifies branch, upstream, working tree, remote tracking state, and divergence risk.
- `tools/ai/run_supervised_phase21_cycle.py`: Orchestrates read-only checks and returns a final pass/fail result.

## Commit Readiness Meaning

Commit readiness means the repository is ready for a human to review and decide whether to run `git add` and `git commit`. It does not mean the scripts may stage or commit automatically.

A commit-ready Phase 21 state requires:

1. All requested Phase 21 artifacts exist.
2. Python syntax checks pass.
3. The supervised cycle runs in dry-run mode.
4. Known dirty state is limited to intended Phase 21 files.
5. Suspicious files are absent or explicitly reviewed.
6. No generated cache files are present.

## Final Rule

The Phase 21 AI operating loop may observe, validate, summarize, and block. It may not approve, stage, commit, push, release, deploy, delete, or mutate secrets.
