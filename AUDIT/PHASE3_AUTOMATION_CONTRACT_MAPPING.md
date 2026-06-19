# Phase 3B — Automation Contract Mapping

## Objective

Phase 3B documents the operational contract mapping for repository automation after completion of Phase 3A.

This document maps each active workflow to its purpose, enforcement posture, expected trigger behavior, and known repository artifacts.

No enforcement changes are introduced by this document.

## Current Automation Contract Summary

The repository currently uses a conservative automation model:

- Required checks are limited to core safety and release readiness gates.
- Additional operational workflows remain active but non-required.
- Evidence and inventory are recorded under `AUDIT`.
- Future enforcement changes should be introduced only after observation and explicit approval.

## Required Automation Contracts

The active `main` ruleset requires the following status checks:

| Required Check Context | Workflow | Contract Purpose | Enforcement |
| --- | --- | --- | --- |
| `hardening-tests` | `Hardening Tests` | Validate hardening and baseline safety behavior | required |
| `policy-smokes` | `Policy Smoke Tests` | Validate policy smoke expectations | required |
| `Assert release readiness contract` | `Release Readiness Gate` | Validate release readiness contract | required |

These required checks form the current enforced automation baseline.

## Non-Required Automation Contracts

The following workflows are active but not required by the `main` ruleset:

| Workflow | Contract Purpose | Enforcement |
| --- | --- | --- |
| `Operational Roadmap Gate` | Validate repository operational roadmap alignment | non-required |
| `PR Hygiene Gate` | Validate PR and issue hygiene baseline artifacts | non-required |
| `Dependency Graph` | Provide dependency graph visibility | non-required |

These workflows provide useful signals without expanding required enforcement.

## Workflow-to-Contract Mapping

### Hardening Tests

| Field | Value |
| --- | --- |
| Workflow | `Hardening Tests` |
| Expected workflow file | `.github/workflows/hardening-tests.yml` |
| Required status context | `hardening-tests` |
| Enforcement | required |
| Contract category | safety / hardening |
| Primary purpose | Validate hardening-related repository expectations |
| Current posture | enforced by active `main` ruleset |

### Policy Smoke Tests

| Field | Value |
| --- | --- |
| Workflow | `Policy Smoke Tests` |
| Expected workflow file | `.github/workflows/policy-smokes.yml` |
| Required status context | `policy-smokes` |
| Enforcement | required |
| Contract category | policy validation |
| Primary purpose | Validate policy smoke expectations |
| Current posture | enforced by active `main` ruleset |

### Release Readiness Gate

| Field | Value |
| --- | --- |
| Workflow | `Release Readiness Gate` |
| Expected workflow file | `.github/workflows/release-readiness.yml` |
| Required status context | `Assert release readiness contract` |
| Enforcement | required |
| Contract category | release readiness |
| Primary purpose | Validate release readiness contract before protected branch integration |
| Current posture | enforced by active `main` ruleset |

### Operational Roadmap Gate

| Field | Value |
| --- | --- |
| Workflow | `Operational Roadmap Gate` |
| Expected workflow file | `.github/workflows/operational-roadmap.yml` |
| Required status context | none |
| Enforcement | non-required |
| Contract category | operational alignment |
| Primary purpose | Validate that repository operational roadmap expectations remain aligned |
| Current posture | active observational signal |

### PR Hygiene Gate

| Field | Value |
| --- | --- |
| Workflow | `PR Hygiene Gate` |
| Expected workflow file | `.github/workflows/pr-hygiene.yml` |
| Required status context | none |
| Enforcement | non-required |
| Contract category | contribution hygiene |
| Primary purpose | Validate PR template, issue templates, and CODEOWNERS hygiene baseline |
| Validation script | `tools/assert_pr_hygiene.ps1` |
| Current posture | active observational signal |

### Dependency Graph

| Field | Value |
| --- | --- |
| Workflow | `Dependency Graph` |
| Expected workflow file | `.github/workflows/dependency-graph.yml` |
| Required status context | none |
| Enforcement | non-required |
| Contract category | dependency visibility |
| Primary purpose | Provide dependency graph visibility |
| Current posture | active observational signal |

## PR Hygiene Contract Details

The PR hygiene contract currently validates the presence and expected content of:

- `.github/CODEOWNERS`
- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/bug_report.yml`
- `.github/ISSUE_TEMPLATE/automation_request.yml`
- `.github/ISSUE_TEMPLATE/documentation_request.yml`
- `.github/ISSUE_TEMPLATE/config.yml`

Validation script:

- `tools/assert_pr_hygiene.ps1`

Expected successful output:
```text
PR HYGIENE GATE: PASS

## Enforcement Boundary

The following checks are required:

- `hardening-tests`
- `policy-smokes`
- `Assert release readiness contract`

The following checks/signals are active but non-required:

- `Assert operational roadmap contract`
- `Assert PR hygiene contract`
- `Dependency Graph`

This boundary should remain unchanged unless a future phase explicitly approves an enforcement expansion.

## Traceability to Prior Evidence

Related audit documents:

- `AUDIT/PHASE2C_PR_HYGIENE_EVIDENCE.md`
- `AUDIT/PHASE2_AUTOMATION_CLOSURE.md`
- `AUDIT/PHASE3_OPERATIONAL_INVENTORY.md`

Related merged PRs:

- `#20` — PR and issue hygiene baseline
- `#21` — PR hygiene validation gate
- `#22` — PR hygiene evidence documentation
- `#23` — Phase 2 automation closure snapshot
- `#24` — Phase 3 operational inventory

## Validation Commands

Use the following commands to confirm the mapped state:

bash
git status -sb
gh workflow list
gh api repos/cosmicpatternsystem-ui/s43-refactor/rulesets/17888945 --jq '.rules[]? | select(.type=="required_status_checks")'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\assert_pr_hygiene.ps1

## Operational Guidance

For future automation additions:

1. Add the workflow as active but non-required.
2. Document the intended contract.
3. Add a validation script when practical.
4. Observe behavior across pull requests.
5. Record evidence in `AUDIT`.
6. Only then consider required enforcement changes.

## Final Assessment

Phase 3B establishes a contract mapping baseline for active repository automation.

No ruleset, branch protection, workflow, or required status check changes are introduced.
