# Autonomous Follow-up Checklist

This checklist defines the minimum safe continuation protocol for autonomous follow-up work after a governance PR has been merged.

## Purpose

Autonomous follow-up work must start from a clean, synchronized, validated repository state and must preserve the project constitution, canonical source hierarchy, roadmap contract, and governance hardening guarantees.

## Required Starting State

Before making changes, verify:

- The active branch is not `main`.
- The branch is based on the latest `origin/main`.
- The working tree is clean.
- The branch has an upstream remote tracking branch.
- Baseline governance validation passes locally.

## Baseline Commands

Required baseline validation:
```powershell
git fetch origin --prune
git pull --ff-only
python tools/governance_hardening_check.py
python tools/project_constitution_check.py
python -m pytest tests/test_governance_hardening_pack.py tests/test_project_constitution_pack.py tests/test_governance_bootstrap.py -q
git diff --check
git status --short

## Patch Rules

Each autonomous follow-up patch must:

- Modify the smallest practical set of files.
- Preserve BOM-free UTF-8 with LF line endings.
- Keep generated artifacts out of source unless explicitly required.
- Avoid weakening validators, gates, contracts, or governance workflows.
- Prefer additive documentation or contract-safe changes unless a validator requires code changes.
- Keep the repository recoverable through Git history.

## Validation Rules

Before commit, run:

powershell
python tools/governance_hardening_check.py
python tools/project_constitution_check.py
python -m pytest tests/test_governance_hardening_pack.py tests/test_project_constitution_pack.py tests/test_governance_bootstrap.py -q
git diff --check

## Commit Readiness

A patch is ready to commit only when:

- Local validation is green.
- `git diff --check` reports no whitespace errors.
- `git status --short` contains only intentional files.
- The commit message describes the governance-safe intent.

## PR Readiness

A follow-up PR is ready only when:

- The branch is pushed to origin.
- CI reports all required checks successful.
- The PR description identifies the validation commands run locally.
- The PR does not introduce undocumented governance bypasses.

## Failure Handling

If validation fails:

- Stop further changes.
- Identify the failing validator or test.
- Patch the smallest direct cause.
- Re-run the full baseline validation.
- Do not commit partial or speculative fixes.