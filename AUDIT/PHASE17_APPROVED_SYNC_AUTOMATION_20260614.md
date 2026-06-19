# Phase 17 Approved Sync Automation

Date: 2026-06-14
Branch: phase17-work-from-restore

## Purpose

This document records the approved Phase 17 synchronization policy for storing final-approved changes on both the local laptop repository and GitHub.

## Decision

Manual `git add`, `git commit`, and `git push` must not be the default finalization path for Phase 17 operational work.

Final-approved changes should be synchronized through:
```text
tools/phase17_approved_sync.ps1

## Required Behavior

The approved sync tool must:

- Verify the current branch.
- Accept an explicit commit message.
- Accept an explicit list of approved paths.
- Refuse to continue if unapproved working tree changes are present.
- Run the Phase 17 quality gate before commit.
- Stage only approved paths.
- Reject staged whitespace errors.
- Create the commit locally.
- Run the Phase 17 health check after commit.
- Push to GitHub only after the post-commit health check passes.

## Safety Model

The tool intentionally avoids blind repository-wide staging.

This protects the repository from accidentally committing unrelated local files, temporary files, or incomplete work.

## Baseline Policy

For the current Phase 17 baseline, the default health-check mode is:

text
PreRestart

This matches the documented one-shot behavior of:

text
tools/safe_auto_snapshot_phase17.ps1

## Manual Push Note

Commit `1201658` was pushed manually because the approved sync automation did not exist yet.

From the introduction of `tools/phase17_approved_sync.ps1` onward, final-approved local and GitHub synchronization should be performed through the approved sync tool unless an emergency manual action is explicitly documented.
