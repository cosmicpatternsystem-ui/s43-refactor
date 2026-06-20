# Operational Continuity Runbook

## Purpose

This runbook describes how to preserve operational continuity for the repository
while keeping the existing enforcement model unchanged.

## Scope

This runbook applies to documentation, review, validation, and merge practices
that support continuity of repository operations.

It does not change:

- rulesets
- branch protection
- required status checks
- workflow definitions
- validation scripts
- automation gate behavior

## Continuity Objectives

Operational continuity for this repository means:

- repository validation remains available and observable
- required checks continue to run as expected
- documentation updates remain compatible with existing automation
- pull requests follow consistent hygiene and merge discipline
- governance and maintenance records remain traceable over time

## Baseline References

Primary continuity references include:

- `docs/OPERATIONAL_CONTINUITY.md`
- `AUDIT/PHASE7A_OPERATIONAL_CONTINUITY_BASELINE.md`
- `AUDIT/PHASE7B_OPERATIONAL_CONTINUITY_EVIDENCE_SNAPSHOT.md`

## Standard Operating Procedure

### 1. Start From Updated Main

Before making continuity-related documentation changes:

- switch to `main`
- pull latest remote changes with fast-forward only
- confirm local branch alignment with `origin/main`

Example:
```bash
git checkout main
git pull --ff-only origin main
git status -sb

Expected result:

- local `main` is aligned with `origin/main`

### 2. Create Isolated Working Branch

Create a dedicated branch for the continuity documentation update.

Example:

bash
git checkout -b automation/phase7-operational-continuity-<topic>

### 3. Preserve Documentation-Only Scope

Allowed changes include:

- `docs/`
- `AUDIT/`

Continuity documentation updates must not modify:

- `.github/workflows/`
- `tools/`
- ruleset configuration
- branch protection settings
- required status check configuration
- merge enforcement behavior

Recommended verification:

bash
git diff --name-only
git diff --name-only | grep -E '^(\.github/workflows/|tools/)' && echo "UNEXPECTED ENFORCEMENT FILE CHANGE" || echo "OK: documentation-only file scope"

### 4. Validate Pull Request Hygiene Locally

Before opening a PR, run the existing local hygiene validation.

Example:

bash
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/assert_pr_hygiene.ps1

Expected result:

- `PR HYGIENE GATE: PASS`

### 5. Commit With Clear Documentation Intent

Use a documentation-focused commit message that reflects the continuity purpose.

Example patterns:

- `docs: add operational continuity runbook`
- `docs: update operational continuity guidance`

### 6. Open Pull Request With Explicit Non-Change Statement

The pull request description should explicitly state:

- documentation-only scope
- no changes to enforcement
- no changes to workflow files
- no changes to validation scripts
- no changes to required checks
- no changes to branch protection or rulesets

### 7. Observe Repository Checks

After PR creation, observe the existing repository checks and allow them to run unchanged.

Expected workflow visibility includes:

- `Hardening Tests`
- `Operational Roadmap Gate`
- `Policy Smoke Tests`
- `PR Hygiene Gate`
- `Release Readiness Gate`

Expected required checks baseline includes:

- `hardening-tests`
- `policy-smokes`
- `Assert release readiness contract`

### 8. Merge Only After Successful Checks

Merge only when expected required checks complete successfully.

Preferred merge style used in this repository flow:

- squash merge

### 9. Reconfirm Main Alignment After Merge

After merge:

- return to `main`
- pull latest remote changes
- confirm `main` remains aligned with `origin/main`

Example:

bash
git checkout main
git pull --ff-only origin main
git status -sb

### 10. Record Closure Evidence

Capture closure evidence showing:

- merge completion
- main branch alignment
- recent commit history
- workflow visibility
- unchanged ruleset/repository enforcement posture

## Continuity Guardrails

Operational continuity documentation must preserve these guardrails:

1. No enforcement drift
2. No hidden workflow mutation
3. No validation script alteration
4. No required check redefinition
5. No branch protection weakening
6. No undocumented process deviation

## Failure / Escalation Guidance

Escalate and pause merge activity if any of the following occur:

- unexpected file scope includes workflow or tooling paths
- local PR hygiene validation fails
- expected checks do not start
- required checks fail
- workflow visibility changes unexpectedly
- ruleset or branch protection behavior appears different from baseline

In such cases:

- do not force changes through
- document the observed deviation
- compare against baseline evidence
- resolve the discrepancy before merge

## Final Statement

This runbook preserves repository operational continuity through disciplined,
documentation-only change management within the existing enforcement boundary.
