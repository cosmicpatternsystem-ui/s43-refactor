# Phase 17 Operational Readiness Baseline

Date: 2026-06-14
Branch: phase17-work-from-restore
Purpose: Register the safe operational baseline for Phase 17.

## Verified Baseline

The repository is expected to be operated through the approved sync automation.

Official automation:

- tools/phase17_approved_sync.ps1

Required validation:

- Run enterprise quality gate before commit.
- Commit only approved paths.
- Reject unexpected dirty files.
- Check staged whitespace.
- Run health check after commit.
- Push only after successful health check.
- End with a clean working tree.

## Health Mode Interpretation

Current snapshot behavior is one-shot.

Therefore:

- PreRestart expects zero long-running workers.
- PostStart expects exactly one long-running worker.
- Current operational baseline uses PreRestart.

## GitHub Synchronization Policy

Manual push should not be the normal operating path.

Future official sync should use:

- tools/phase17_approved_sync.ps1
- Explicit approved paths
- Explicit commit message
- HealthMode PreRestart
- Push enabled only after final approval

## Forensic Safety

The project must avoid unsafe cleanup or destructive history operations unless explicitly approved.

Forbidden by default:

- git reset --hard
- git checkout -- for unrelated files
- blind git add .
- silent deletion of unknown files
- unrecorded operational changes

## Current Readiness Statement

Phase 17 is considered operationally ready when all of the following are true:

- Working tree is clean.
- Local branch is phase17-work-from-restore.
- Local HEAD equals origin/phase17-work-from-restore.
- Quality gate passes.
- Health check passes in PreRestart mode.
- Approved sync reports APPROVED_SYNC_PASS.
