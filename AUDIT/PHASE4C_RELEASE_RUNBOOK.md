# Phase 4C — Release Runbook

## Objective

Phase 4C adds an operational release runbook for maintainers.

This phase documents release verification, workflow inspection, required-check inspection, failure response, rollback guidance, and enforcement change policy.

## Scope Completed

This phase adds:

- `docs/RELEASE_RUNBOOK.md`

The runbook documents:

- release operating principles
- pre-release checklist
- workflow inspection
- required check inspection
- release readiness gate expectations
- release pull request checklist
- failure response
- rollback guidance
- enforcement change policy
- out-of-scope release automation

## Current Required Check Baseline

The current required protected-branch checks remain:

- `hardening-tests`
- `policy-smokes`
- `Assert release readiness contract`

The strict required status check policy remains:

- `strict_required_status_checks_policy: false`

## Current Non-Required Automation

The following automation remains active but non-required:

- `Assert operational roadmap contract`
- `Assert PR hygiene contract`
- `Dependency Graph`

## Relationship to Phase 4A and Phase 4B

Phase 4C builds on:

- `docs/RELEASE_PROCESS.md`
- `AUDIT/PHASE4A_RELEASE_DOCUMENTATION_BASELINE.md`
- `AUDIT/PHASE4B_RELEASE_EVIDENCE_SNAPSHOT.md`

Phase 4A established the release documentation baseline.

Phase 4B recorded evidence for that baseline.

Phase 4C adds maintainer-facing operational release guidance.

## Safety Statement

This phase is documentation-only.

No changes were made to:

- `.github/workflows/*`
- `tools/*`
- repository rulesets
- branch protection behavior
- required status checks
- workflow enforcement classification
- release automation
- tag automation
- versioning automation

## Validation Expectations

Validation for this phase consists of:

- local PR hygiene assertion
- successful pull request checks
- confirmation that workflow and ruleset posture remain unchanged

## Final Assessment

Phase 4C establishes the release runbook while preserving the existing conservative automation and enforcement posture.
