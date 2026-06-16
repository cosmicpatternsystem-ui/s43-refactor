# Next Action

Status: MANDATORY
Current Phase: Phase 21
Allowed Track: Release Automation Dry-Run Design
Production Release: BLOCKED
Risky Refactor: BLOCKED
Manual Phase Closure: INVALID
Branch Protection Enforcement: REQUIRED BEFORE PRODUCTION RELEASE

## Binding Roadmap

The binding commercial-grade roadmap is recorded in:

AUDIT/COMMERCIAL_MANDATORY_ROADMAP.md

This roadmap is mandatory and repository-wide.

Any action that conflicts with the roadmap is invalid, even if local tests pass.

## Current Authorized Next Action

Phase 21: Release Automation Dry-Run Design

The next patch may only create or update non-destructive release dry-run design artifacts.

## Objective

Design the release automation flow as a dry-run only process.

The process must document what would happen during release automation without performing any production release, irreversible change, risky refactor, destructive migration, or secrets modification.

## Allowed Work

1. Documentation.
2. Non-destructive dry-run scripts.
3. Release checklist design.
4. Rollback checklist design.
5. Stop-condition design.
6. Approval-flow design.
7. Audit-trail improvement.
8. Release preflight documentation.
9. Post-release verification design.
10. Incident response draft.

## Expected Phase 21 Artifacts

Expected artifacts may include:

1. AUDIT/PHASE21_RELEASE_AUTOMATION_DRY_RUN_DESIGN_<timestamp>.md
2. tools/Invoke-ReleaseDryRun.ps1
3. documentation describing release preflight checks
4. documentation describing rollback and stop conditions
5. documentation describing release approval flow
6. documentation describing post-release verification

## Forbidden Work

The following actions remain forbidden:

1. Production release.
2. Real deployment.
3. Risky refactor.
4. Destructive migration.
5. Secrets modification.
6. Irreversible automation.
7. Direct release from local machine.
8. Manual phase closure.
9. Bypassing quality gates.
10. Declaring commercial readiness without evidence.

## Phase Closure Rule

No phase closure is valid unless performed through the operational runner:

tools/Invoke-OperationalPhaseClose.ps1

A valid close must include:

1. Quality gate pass.
2. Audit update.
3. Commit creation.
4. Push to remote.
5. Remote synchronization verification.
6. Final operational close signal.

## Final Rule

If there is a conflict between speed and safety, safety wins.

If there is a conflict between local success and audit evidence, audit evidence wins.

If there is a conflict between manual action and operational runner closure, operational runner closure wins.

Proceed only with Phase 21 release automation dry-run design.

# Non-Negotiable Completion Rule

Every meaningful change must end with the agent running:

    .\tools\Invoke-SafeSyncAndBackup.ps1 -CommitMessage "<completed change>"

The agent must not mark work as complete unless the workflow reports:

    SAFE SYNC AND DISASTER RECOVERY BACKUP COMPLETE
    Workspace: clean
    Remote: synced

The final answer must include the final commit hash and physical backup path.
