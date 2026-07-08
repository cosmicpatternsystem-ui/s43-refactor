# Autonomous Failure Handling Runbook

## Purpose

This runbook defines the required operator response when autonomous governance validation, test execution, merge readiness, or repository synchronization fails.

It is intended for post-merge and pre-PR workflows where the repository must remain reviewable, recoverable, and safe for concurrent work.

## Starting Assumptions

- Work is performed on a feature or governance branch, not directly on `main`.
- `main` is synchronized with `origin/main` before branch creation.
- The working tree is clean before applying a patch.
- Validation failures are fixed forward in the active branch.
- No destructive Git operation is allowed unless explicitly approved.

## Failure Classes

### Synchronization Failure

Examples:

- `git pull --ff-only` fails.
- The branch is behind or diverged.
- Remote references are stale.
- The expected base commit is not present.

Required response:

1. Stop patch work.
2. Run `git status --short`.
3. Run `git branch --show-current`.
4. Run `git fetch origin --prune`.
5. Inspect divergence before changing files.
6. Do not rebase, reset, or force-push without explicit approval.

### Validation Failure

Examples:

- `tools/governance_hardening_check.py` fails.
- `tools/project_constitution_check.py` fails.
- Required governance files or markers are missing.
- Canonical source expectations are not satisfied.

Required response:

1. Treat the failure as authoritative.
2. Read the failing message before editing.
3. Apply the smallest fix that restores the declared contract.
4. Re-run the exact failing command.
5. Re-run the full baseline validation set before commit.

### Test Failure

Examples:

- Pytest exits non-zero.
- A governance test fails after a documentation or contract change.
- A fixture no longer matches expected repository structure.

Required response:

1. Identify whether the failure is caused by the current patch.
2. Fix implementation, documentation, or test expectations only within the patch scope.
3. Do not weaken tests to make an unrelated change pass.
4. Re-run the targeted test first.
5. Re-run the full baseline test set before commit.

### Whitespace Or Encoding Failure

Examples:

- `git diff --check` reports trailing whitespace.
- A file is written with an unexpected BOM.
- Line endings drift from LF.

Required response:

1. Normalize the changed file to UTF-8 without BOM.
2. Normalize line endings to LF.
3. Re-run `git diff --check`.
4. Confirm the diff only contains intentional content changes.

### PR Readiness Failure

Examples:

- CI is pending or failing.
- The PR branch is not up to date.
- The PR contains unrelated files.
- The PR title or body does not describe the actual patch.

Required response:

1. Do not merge.
2. Inspect failing checks.
3. Keep the PR branch focused on one atomic change.
4. Push only the minimum fix required.
5. Wait for required checks to pass before merge.

## Baseline Recovery Commands

Run these commands after any failure has been fixed:
```powershell
git fetch origin --prune
git status --short
git branch --show-current

python tools/governance_hardening_check.py
python tools/project_constitution_check.py
python -m pytest tests/test_governance_hardening_pack.py tests/test_project_constitution_pack.py tests/test_governance_bootstrap.py -q
git diff --check
git status --short

## Stop Conditions

Stop and escalate before continuing if any of the following are true:

- The active branch is not the expected working branch.
- The working tree contains unrelated changes.
- `main` and `origin/main` have diverged.
- A fix requires changing canonical contracts outside the patch scope.
- A destructive Git command appears necessary.
- A force push appears necessary.
- Validation output is ambiguous or contradicts repository documentation.

## Commit Readiness

A commit is ready only when:

- The patch is atomic.
- The working branch is correct.
- The diff contains only intentional files.
- Governance validation passes.
- Constitution validation passes.
- Required tests pass.
- `git diff --check` is clean.
- The commit message describes the behavior or document added.

## PR Readiness

A PR is ready only when:

- The branch is pushed to origin.
- The PR targets `main`.
- The PR title matches the commit scope.
- The PR body lists the local validation commands.
- CI is green or actively being monitored.
- No unrelated branch cleanup is mixed into the PR.