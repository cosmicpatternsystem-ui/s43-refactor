# Operational Continuity

## Purpose

This document defines the repository operational continuity baseline.

Operational continuity ensures that repository stewardship can continue safely
after governance, release, and maintenance documentation phases have been
established.

## Scope

This document is documentation-only.

It does not modify:

- GitHub rulesets
- branch protection
- required status checks
- workflow files
- validation scripts
- automation behavior

## Continuity Objectives

The operational continuity model is intended to preserve:

- visibility into repository health
- consistency of documentation expectations
- awareness of required checks
- awareness of active workflows
- predictable pull request hygiene
- traceability of documentation-only changes
- safe escalation when drift is observed

## Repository Health Signals

Routine continuity review should observe the following signals:

- `main` is aligned with `origin/main`
- working tree is clean before new documentation work starts
- expected workflows remain active
- required status checks remain unchanged unless intentionally updated through a separate enforcement change process
- documentation-only phases do not modify enforcement files
- pull requests receive expected repository checks

## Active Workflow Awareness

The active workflow baseline is expected to include:

- `Hardening Tests`
- `Operational Roadmap Gate`
- `Policy Smoke Tests`
- `PR Hygiene Gate`
- `Release Readiness Gate`
- `Dependency Graph`

This document records the expected workflow visibility only. It does not modify
workflow configuration.

## Required Status Check Awareness

The required status check baseline is expected to include:

- `hardening-tests`
- `policy-smokes`
- `Assert release readiness contract`

The strict required status checks policy is expected to remain:

- `strict_required_status_checks_policy: false`

This document records the expected required check visibility only. It does not
modify ruleset configuration.

## Documentation-Only Change Expectations

Operational continuity documentation changes should:

- use a dedicated branch
- add or update documentation files only
- avoid workflow file changes
- avoid validation script changes
- avoid ruleset or branch protection changes
- run local PR hygiene validation when available
- open a pull request for review and repository checks
- merge only after expected checks complete successfully

## Enforcement Boundary

Operational continuity documentation must not be used as a substitute for an
enforcement change.

Any intentional change to repository enforcement should be handled separately
from documentation-only continuity work.

Examples of enforcement changes include:

- changing required status checks
- editing workflow files
- changing validation scripts
- changing rulesets
- changing branch protection behavior
- changing automation gates

## Drift Review

A continuity review should treat the following as possible drift indicators:

- missing expected workflows
- unexpected required status checks
- disabled workflow visibility
- changed strict required status check policy
- documentation pull requests modifying `.github/workflows/`
- documentation pull requests modifying `tools/`
- checks missing from pull request status
- local validation failing unexpectedly

## Escalation

If drift is observed, the recommended response is:

1. stop the documentation-only change
2. do not merge the pull request
3. capture the observed drift in an audit note
4. verify whether the drift is intentional
5. separate enforcement remediation from documentation-only work

## Continuity Checklist

Before opening a documentation-only continuity pull request:

- confirm branch is based on current `main`
- confirm working tree starts clean
- confirm changed files are documentation/audit files only
- confirm no workflow files changed
- confirm no validation scripts changed
- run local PR hygiene validation when available
- create a pull request
- wait for repository checks to complete

After merge:

- return to `main`
- pull with `--ff-only`
- confirm `main` is aligned with `origin/main`
- confirm recent log includes the merged pull request
- confirm workflows remain active
- confirm required status checks remain unchanged

## Final Statement

Operational continuity preserves repository confidence by keeping routine
documentation work visible, traceable, and separated from enforcement changes.
