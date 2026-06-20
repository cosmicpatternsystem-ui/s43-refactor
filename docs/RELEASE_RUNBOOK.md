# Release Runbook

## Objective

This runbook describes the operational steps maintainers should follow when preparing, validating, and completing a repository release.

This document is operational guidance only. It does not introduce release automation or change repository enforcement.

## Release Operating Principles

Maintainers should keep release activity:

- traceable to `main`
- validated by required checks
- reviewable through pull requests when release changes are needed
- aligned with the documented release process
- conservative with respect to enforcement changes

## Pre-Release Checklist

Before preparing a release, verify the local repository state:
```bash
git checkout main
git pull --ff-only origin main
git status -sb
git log --oneline -10

Expected result:

- local `main` matches `origin/main`
- working tree is clean
- recent history includes the intended release changes

## Workflow Inspection

Verify active workflows:

bash
gh workflow list

Expected active workflows:

- `Hardening Tests`
- `Operational Roadmap Gate`
- `Policy Smoke Tests`
- `PR Hygiene Gate`
- `Release Readiness Gate`
- `Dependency Graph`

If an expected workflow is missing or inactive, pause release activity and investigate before proceeding.

## Required Check Inspection

Verify the current required protected-branch checks:

bash
gh api repos/cosmicpatternsystem-ui/s43-refactor/rulesets/17888945 \
  --jq '.rules[]? | select(.type=="required_status_checks")'

Expected required checks:

- `hardening-tests`
- `policy-smokes`
- `Assert release readiness contract`

Expected strict policy setting:

- `strict_required_status_checks_policy: false`

If required checks differ unexpectedly, pause release activity and review the ruleset change history.

## Release Readiness Gate

The release baseline relies on the active workflow:

- `Release Readiness Gate`

The required check is:

- `Assert release readiness contract`

A release should not proceed if this required check is failing.

## Release Pull Request Checklist

When a release-related pull request is needed, include:

- release intent
- validation evidence
- relevant workflow results
- confirmation that required checks passed
- confirmation that no unintended enforcement changes were introduced
- any known operational risks

## Failure Response

If a required check fails:

1. Do not bypass the failure.
2. Inspect the workflow logs.
3. Identify whether the failure is caused by repository content, workflow configuration, or external service behavior.
4. Fix the issue in a follow-up commit or pull request.
5. Re-run validation.
6. Proceed only after required checks pass.

If a non-required check fails:

1. Inspect the failure for release relevance.
2. Determine whether it indicates a real repository issue.
3. Document the decision in the pull request if proceeding.
4. Avoid changing enforcement in the same pull request.

## Rollback Guidance

If a release-related change needs to be reverted:

1. Prefer a normal revert pull request.
2. Include the original PR or commit reference.
3. Explain the operational reason for rollback.
4. Run the standard required checks.
5. Confirm that release documentation and enforcement posture remain consistent.

Avoid destructive history changes on protected branches.

## Enforcement Change Policy

Release enforcement changes must not be bundled into routine release work.

Any future release enforcement change should use a dedicated pull request and include:

- rationale
- before and after required-check comparison
- ruleset impact assessment
- rollback plan
- maintainer approval

## Out of Scope

This runbook does not add or require:

- automated release publishing
- tag creation automation
- changelog generation automation
- package registry publishing
- artifact publishing automation
- new required checks

## Related Documents

- `docs/RELEASE_PROCESS.md`
- `AUDIT/PHASE4A_RELEASE_DOCUMENTATION_BASELINE.md`
- `AUDIT/PHASE4B_RELEASE_EVIDENCE_SNAPSHOT.md`
- `AUDIT/PHASE3_OPERATIONAL_RUNBOOK.md`

## Final Assessment

This runbook provides operational release guidance while preserving the existing conservative repository automation posture.
