# Phase 3C — Operational Runbook

## Objective

Phase 3C provides an operational runbook for maintainers working with the repository automation baseline.

This document explains how to verify repository state, inspect workflow status, audit required checks, run local validation, and respond to automation failures.

No enforcement changes are introduced by this document.

## Current Operational Baseline

Required checks:

- `hardening-tests`
- `policy-smokes`
- `Assert release readiness contract`

Active non-required automation:

- `Operational Roadmap Gate`
- `PR Hygiene Gate`
- `Dependency Graph`

The active non-required workflows provide visibility without expanding protected-branch enforcement.

## Standard Repository Verification

### Verify Current Branch and Clean Working Tree

Command:

    git status -sb

Expected clean output on `main`:

    ## main...origin/main

If local changes are shown, do not proceed until they are committed, stashed, or intentionally discarded.

### Synchronize main

Commands:

    git checkout main
    git pull --ff-only origin main

Expected result:

    Already up to date.

or a clean fast-forward update.

Avoid non-fast-forward pulls for protected automation work.

### Review Recent History

Command:

    git log --oneline -8

Use this to confirm that recent merged PRs are present and ordered as expected.

## Workflow Verification

List workflow status:

    gh workflow list

Expected active workflows:

- `Hardening Tests`
- `Operational Roadmap Gate`
- `Policy Smoke Tests`
- `PR Hygiene Gate`
- `Release Readiness Gate`
- `Dependency Graph`

If a workflow is disabled unexpectedly, investigate before making automation changes.

## Ruleset Verification

Inspect the active `main` ruleset required status checks:

    gh api repos/cosmicpatternsystem-ui/s43-refactor/rulesets/17888945 --jq '.rules[]? | select(.type=="required_status_checks")'

Expected required checks:

- `hardening-tests`
- `policy-smokes`
- `Assert release readiness contract`

The following should remain non-required unless explicitly approved in a future enforcement phase:

- `Assert PR hygiene contract`
- `Assert operational roadmap contract`
- `Dependency Graph`

## Local PR Hygiene Validation

Run the local PR hygiene assertion:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\assert_pr_hygiene.ps1

Expected successful output:

    PR HYGIENE GATE: PASS

If this fails, check the following files first:

- `.github/CODEOWNERS`
- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/bug_report.yml`
- `.github/ISSUE_TEMPLATE/automation_request.yml`
- `.github/ISSUE_TEMPLATE/documentation_request.yml`
- `.github/ISSUE_TEMPLATE/config.yml`

## Pull Request Verification Procedure

### Create a Dedicated Branch

Commands:

    git checkout main
    git pull --ff-only origin main
    git checkout -b automation/<short-purpose>

### Make the Minimal Change

Prefer small PRs that change one concept at a time.

Examples:

- one documentation update
- one validation script update
- one workflow update
- one audit snapshot

Avoid mixing ruleset changes with unrelated documentation or workflow changes.

### Run Local Validation

At minimum, run:

    git status -sb
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\assert_pr_hygiene.ps1

For future specialized gates, run their corresponding local validation scripts when available.

### Push and Create PR

Commands:

    git push -u origin automation/<short-purpose>
    gh pr create --base main --head automation/<short-purpose>

### Watch PR Checks

Command:

    gh pr checks --watch

Expected required checks should pass:

- `Hardening Tests/hardening-tests`
- `Policy Smoke Tests/policy-smokes`
- `Release Readiness Gate/Assert release readiness contract`

Expected non-required observational checks may also run:

- `Operational Roadmap Gate/Assert operational roadmap contract`
- `PR Hygiene Gate/Assert PR hygiene contract`

## Failure Response Guide

### Hardening Tests Failure

If `hardening-tests` fails:

1. Do not merge.
2. Inspect the workflow logs.
3. Determine whether the failure is caused by the PR or by external infrastructure.
4. Fix the underlying issue in the branch.
5. Re-run checks.
6. Record evidence if the failure affects an audit phase.

### Policy Smoke Tests Failure

If `policy-smokes` fails:

1. Do not merge.
2. Review policy-related expectations.
3. Confirm whether the PR changed policy, workflow, or validation files.
4. Update the PR only if the change is intentional and safe.
5. Re-run checks.

### Release Readiness Failure

If `Assert release readiness contract` fails:

1. Do not merge.
2. Treat as a release-contract issue.
3. Inspect the workflow output carefully.
4. Confirm whether release readiness assumptions changed.
5. Fix the PR or document the required follow-up before proceeding.

### PR Hygiene Gate Failure

If `Assert PR hygiene contract` fails:

1. Check whether PR template, issue templates, or CODEOWNERS changed.
2. Run local validation with `tools/assert_pr_hygiene.ps1`.
3. Restore required phrases or update the contract intentionally in a separate PR.
4. Keep this gate non-required unless a future phase explicitly approves enforcement expansion.

### Operational Roadmap Gate Failure

If `Assert operational roadmap contract` fails:

1. Inspect the roadmap contract expected by the workflow.
2. Confirm whether documentation or roadmap references changed.
3. Fix alignment or document the intended contract update.
4. Keep this gate non-required unless future approval changes enforcement.

## Enforcement Change Policy

Do not change the following without explicit approval:

- active ruleset enforcement
- required status check list
- branch protection behavior
- required workflow contexts
- strict required status check policy

Any future enforcement expansion should follow this sequence:

1. Add or update the workflow as non-required.
2. Run it across multiple PRs.
3. Collect evidence in `AUDIT`.
4. Document the contract.
5. Create a dedicated enforcement proposal.
6. Apply the ruleset change only after approval.

## Documentation Expectations

Current Phase 3 documents:

- `AUDIT/PHASE3_OPERATIONAL_INVENTORY.md`
- `AUDIT/PHASE3_AUTOMATION_CONTRACT_MAPPING.md`
- `AUDIT/PHASE3_OPERATIONAL_RUNBOOK.md`

Related Phase 2 documents:

- `AUDIT/PHASE2C_PR_HYGIENE_EVIDENCE.md`
- `AUDIT/PHASE2_AUTOMATION_CLOSURE.md`

## Recommended Maintenance Cadence

Before each automation PR:

    git status -sb
    gh workflow list
    gh api repos/cosmicpatternsystem-ui/s43-refactor/rulesets/17888945 --jq '.rules[]? | select(.type=="required_status_checks")'
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\assert_pr_hygiene.ps1

After each automation PR merge:

    git checkout main
    git pull --ff-only origin main
    git status -sb
    git log --oneline -8
    gh workflow list

## Final Assessment

Phase 3C establishes a maintainer runbook for operating the repository automation baseline.

No ruleset, branch protection, workflow, script, or required status check changes are introduced.
