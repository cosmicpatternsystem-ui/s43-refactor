# Repository Stewardship Runbook

Date: 2026-06-20

## Purpose
This runbook defines the routine stewardship practices used to preserve repository health, documentation continuity, auditability, and enforcement awareness without changing repository enforcement behavior.

## Stewardship Principles
- preserve repository clarity through documentation-first maintenance
- maintain an auditable change trail through focused PRs
- keep workflow and required check visibility intact
- avoid direct changes to enforcement boundaries unless explicitly authorized
- use small, reviewable documentation-only updates when recording continuity evidence

## Routine Stewardship Activities

### 1. Documentation Review
Regularly review core repository documentation to confirm it remains:
- present
- internally consistent
- aligned with current repository operating expectations

Priority documents include:
- `README.md`
- operational continuity documents
- repository stewardship documents
- audit snapshots
- maintenance runbooks

### 2. Audit Trail Verification
Confirm that recent completed phases have:
- a merged PR
- a clear commit message
- traceable audit documentation
- no unexplained scope expansion

### 3. Workflow Visibility Review
Check that repository workflows remain visible and active, especially:
- Hardening Tests
- Operational Roadmap Gate
- Policy Smoke Tests
- PR Hygiene Gate
- Release Readiness Gate
- Dependency Graph

### 4. Required Check Awareness
Verify that protected branch required checks remain consistent with the established baseline:
- `hardening-tests`
- `policy-smokes`
- `Assert release readiness contract`

### 5. Enforcement Boundary Awareness
Do not modify the following during stewardship-only work:
- rulesets
- branch protection behavior
- workflow definitions
- validation scripts
- required check configuration
- merge policy logic
- automation gate behavior

## Recommended Stewardship Procedure

1. sync local `main` with `origin/main`
2. create a focused branch for a single documentation objective
3. make documentation-only changes
4. verify changed file scope before commit
5. open a PR with a narrow summary
6. observe workflow execution and required checks
7. merge only after expected checks succeed
8. record resulting evidence in audit documentation where applicable

## Escalation Guidance
Escalate before proceeding if any of the following are observed:
- required checks differ from baseline unexpectedly
- workflows disappear or become inactive unexpectedly
- branch protection or ruleset behavior changes
- validation behavior changes outside documentation scope
- automation begins enforcing new conditions not previously documented

## Result
This runbook provides repository stewardship guidance only and does not alter enforcement or automation behavior.
