# Safe Merge Required Check Registration

## Target branch
- `main`

## Required status checks
- `Safe Merge Baseline / safe-merge-baseline`

## Registration authority
- GitHub branch protection or ruleset administrators only

## Enforcement intent
- Pull requests targeting `main` must pass the hosted Safe Merge Baseline workflow before merge.
- Direct pushes to `main` remain disallowed.
- This document records the expected required-check name so automation and audits use a stable contract.

## Verification procedure
1. Open repository branch protection or ruleset configuration for `main`.
2. Register `Safe Merge Baseline / safe-merge-baseline` as a required status check.
3. Open a non-trivial pull request against `main`.
4. Confirm the check appears in the PR status area.
5. Confirm merge is blocked until the check passes.
6. Merge only after all required checks pass.

## Evidence
- Hosted workflow path: `.github/workflows/safe-merge-baseline.yml`
- Local checker path: `tools/safe_merge_check.ps1`
- Contract path: `repo/contracts/SAFE_MERGE_AUTOMATION_SPEC.yaml`