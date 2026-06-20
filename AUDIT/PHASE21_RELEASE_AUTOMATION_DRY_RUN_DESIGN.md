# Phase 21 Release Automation Dry-Run Design

Status: DRAFT FOR AUDIT REVIEW
Phase: 21
Scope: Non-destructive release automation dry-run design
Production Release: BLOCKED WITHOUT APPROVAL
Real Deployment: BLOCKED
Destructive Automation: BLOCKED
Secrets Handling: DO NOT STORE OR PRINT SECRETS

## Purpose

This artifact defines a repo-centric dry-run release automation design for Phase 21. It extends the existing timestamped dry-run design by focusing on reusable automation behavior, synchronization safety, approval gates, and evidence expectations. It does not authorize any real release, deployment, publish, tag, push, migration, or production mutation.

## Design Goals

1. Prove that release automation can be audited before it can mutate state.
2. Keep the dry-run local, deterministic, and non-destructive.
3. Fail closed when repository sync or working tree state is unsafe.
4. Produce clear pass/fail output and durable audit evidence.
5. Separate simulated release actions from real release actions.
6. Require human approval before any external or destructive action.

## Non-Goals

This design does not perform or authorize:

- Git push, tag creation, branch creation, merge, rebase, reset, checkout, or clean.
- GitHub release publication.
- Package publication.
- Production deployment.
- Database migration.
- Secret mutation.
- Financial transaction or ledger change.
- Branch protection or CI policy modification.

## Dry-Run Modes

### Read-Only Assessment Mode

Reads repository state and required audit files. Writes nothing. This mode is safe for routine preflight.

Expected command shape:

```text
python3 tools/ai/verify_repo_sync.py
```

### Local Evidence Mode

May write audit artifacts under an approved `AUDIT/PHASE21_*` path after explicit operator approval. It must not modify external systems.

Expected behavior:

- Create timestamped evidence files.
- Record commands executed.
- Record simulated actions.
- Preserve stop-condition output.

### Prohibited Real Release Mode

Any mode that pushes, tags, deploys, publishes, migrates, or mutates production is prohibited during Phase 21.

## Required Preflight

A release dry-run must check:

1. Repository path.
2. Current branch.
3. Current commit.
4. Configured upstream.
5. Remote-tracking ref availability.
6. Working tree status.
7. Ahead and behind counts.
8. Divergence risk.
9. Required audit artifacts.
10. Approval records for any local artifact generation.

The sync verifier must run before any dry-run claims release readiness.

## Simulated Release Flow

The dry-run may print or record the actions that a real release would perform:

1. Validate branch and upstream.
2. Validate clean repository state.
3. Validate required audit and governance artifacts.
4. Validate CI and quality-gate evidence where available.
5. Build a release candidate checklist.
6. Generate release notes preview from local metadata.
7. Simulate release branch naming.
8. Simulate tag naming.
9. Simulate artifact manifest generation.
10. Simulate publication and post-release verification steps.

Every simulated action must be labeled `SIMULATED` and must not execute the underlying release command.

## Forbidden Command Patterns

Dry-run automation must not execute commands that match these intent categories:

- Commit: `git add`, `git commit`.
- Remote mutation: `git push`, release publish, package publish, upload.
- State rewrite: `git reset`, `git clean`, force push, history rewrite.
- Branch or tag mutation: branch creation, branch deletion, tag creation, tag deletion.
- Working tree switching: `git checkout`, `git switch`.
- Production mutation: deploy, migrate, secret update, infrastructure apply.

If a dry-run document references these commands for explanation, they must appear as examples only and must not be executed by automation.

## Stop Conditions

The dry-run must fail and stop if:

1. The current directory is not a Git work tree.
2. The branch is detached or unexpected.
3. Upstream is missing.
4. Remote-tracking state is missing.
5. Working tree is dirty outside documented local dry-run allowance.
6. Branch is behind upstream.
7. Branch is ahead of upstream without explicit local dry-run allowance.
8. Branch is divergent.
9. Required governance artifacts are missing.
10. Any command would mutate remote, production, financial, or secret state.

## Allowed Dry-Run Exceptions

The following exceptions may be documented for local artifact drafting only:

- Dirty working tree caused by known Phase 21 files.
- Ahead branch caused by approved local commits not yet pushed.

These exceptions must be explicitly named in the verifier invocation or audit handoff. They do not authorize release readiness, production action, or commit readiness.

## Approval Gates

### Dry-Run Design Approval

Required before implementing new dry-run automation.

Evidence:

- Scope and non-goals.
- Forbidden command list.
- Stop conditions.
- Expected outputs.
- Validation method.

### Local Evidence Approval

Required before a dry-run writes local audit artifacts.

Evidence:

- Target artifact path.
- Clean or documented dirty state.
- Confirmation that external systems will not be changed.

### Release Execution Approval

Out of scope for Phase 21. A future real release requires separate approval with CI, security, rollback, observability, and incident readiness evidence.

## Expected Outputs

A dry-run should produce clear console output:

```text
PASS: branch has configured upstream
PASS: working tree is clean
PASS: branch is synchronized with upstream
FAIL: release readiness blocked by missing approval
RESULT: FAIL
```

For local evidence mode, the audit artifact should include:

- Timestamp.
- Repository path.
- Branch and commit.
- Upstream.
- Ahead and behind counts.
- Dirty status.
- Simulated actions.
- Stop conditions.
- Result.

## Verification Plan

Minimum validation for Phase 21:

```text
python3 -m py_compile tools/ai/verify_repo_sync.py
python3 tools/ai/verify_repo_sync.py --allow-dirty
```

The `--allow-dirty` condition is acceptable during Phase 21 artifact drafting because the repository contains intentionally untracked Phase 21 audit and tooling files. It is not acceptable for final release readiness.

## Relationship To Existing Artifacts

This design should be read with:

- `AUDIT/PHASE21_AI_SUPERVISOR_TOOLING_ADOPTION.md`
- `AUDIT/PHASE21_RELEASE_AUTOMATION_DRY_RUN_DESIGN_20260616_023808.md`
- `AUDIT/PHASE21_AUTONOMOUS_OPERATION_GOVERNANCE.md`
- `AUDIT/PHASE21_LOCAL_REMOTE_SYNC_RUNBOOK.md`
- `AUDIT/PHASE21_LONG_TERM_AUTONOMOUS_FINANCIAL_SYSTEM_VISION.md`

## Exit Criteria

The Phase 21 dry-run design is ready for review when:

1. The sync verifier exists and is non-destructive.
2. The sync verifier syntax check passes.
3. The sync verifier reports dirty state unless explicitly allowed.
4. Documentation explains allowed dry-run exceptions.
5. `git status --short` lists only expected pending artifacts.
6. No commit, push, tag, deploy, or secret action has been performed.

## Final Rule

A release dry-run may prove readiness to review. It may not perform the release.
