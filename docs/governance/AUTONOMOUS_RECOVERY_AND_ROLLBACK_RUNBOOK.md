# Autonomous Recovery and Rollback Runbook

## Purpose

This runbook defines the required recovery and rollback procedure for autonomous governance changes.

It is designed to preserve repository integrity, artifact continuity, auditability, and safe operational recovery after a failed validation, failed pull request, failed merge, or unsafe working-tree state.

## Scope

This runbook applies to autonomous governance work involving:

- Governance documentation changes
- Constitution and policy changes
- Validation tooling changes
- Test coverage changes
- Pull request preparation
- Post-merge verification
- Branch cleanup and recovery

## Recovery Principles

Autonomous recovery must follow these principles:

1. Never overwrite evidence.
2. Never force-push to shared branches.
3. Never rewrite `main`.
4. Never continue from an unknown repository state.
5. Always preserve local changes before destructive actions.
6. Always validate before commit, push, pull request, and merge.
7. Always recover from `main` only after it is synchronized with `origin/main`.
8. Always prefer small, reviewable patches.
9. Always use timestamped branches for new work.
10. Always leave the repository clean after recovery.

## Stop Conditions

Stop immediately if any of the following occur:

- Working tree contains unexpected changes.
- `git status --short` shows unknown files not created by the current task.
- Validation failures are not understood.
- `git pull --ff-only` fails.
- Branch ancestry is unclear.
- A merge conflict occurs.
- A command attempts to rewrite `main`.
- A command requires `--force` or `--force-with-lease`.
- Test failures appear unrelated to the current change.
- Remote branch state differs from local assumptions.

When a stop condition is encountered, do not continue with commit, push, pull request creation, or merge.

## Baseline Recovery Procedure

Use this procedure to return to a known-good baseline before starting new autonomous work.
```powershell
git switch main
git fetch origin --prune
git pull --ff-only origin main
git status --short
git log -1 --oneline
python tools/governance_hardening_check.py
python tools/project_constitution_check.py
python -m pytest tests/test_governance_hardening_pack.py tests/test_project_constitution_pack.py tests/test_governance_bootstrap.py -q
git diff --check
git status --short

The expected result is:

- `main` is up to date with `origin/main`
- working tree is clean
- governance hardening check passes
- project constitution check passes
- test suite passes
- whitespace check is clean

## Local Change Preservation

If local changes exist and must be preserved, create an evidence branch before any cleanup.

powershell
$branch = "recovery/preserve-local-$(Get-Date -Format yyyyMMdd-HHmmss)"
git switch -c $branch
git add -A
git commit -m "Preserve local recovery state"
git push -u origin $branch

After preservation, open a separate review path for the evidence branch.

## Safe Rollback Procedure

If the current autonomous patch is unsafe before commit, discard only the files intentionally changed by the current task.

powershell
git status --short
git restore -- docs/governance/AUTONOMOUS_RECOVERY_AND_ROLLBACK_RUNBOOK.md
git status --short

If multiple files were changed intentionally, restore each file explicitly.

Do not use broad destructive cleanup commands unless the complete working-tree state has been reviewed and preserved.

## Failed Validation Recovery

If validation fails after a change:

1. Capture the failing command and output.
2. Inspect only the files changed by the current patch.
3. Fix the smallest possible issue.
4. Re-run the full validation set.
5. Do not commit until all required checks pass.

Required validation set:

powershell
python tools/governance_hardening_check.py
python tools/project_constitution_check.py
python -m pytest tests/test_governance_hardening_pack.py tests/test_project_constitution_pack.py tests/test_governance_bootstrap.py -q
git diff --check
git status --short

## Failed Push Recovery

If push fails:

1. Do not force-push.
2. Fetch remote state.
3. Confirm branch tracking.
4. Confirm that `main` has not moved unexpectedly.
5. Rebase only if the branch is private and the operation is clearly safe.
6. Otherwise create a fresh timestamped branch from synchronized `main`.

Safe fresh-branch path:

powershell
git switch main
git fetch origin --prune
git pull --ff-only origin main
$branch = "governance/autonomous-next-$(Get-Date -Format yyyyMMdd-HHmmss)"
git switch -c $branch
git push -u origin $branch

## Failed Pull Request Recovery

If pull request checks fail:

1. Read the failed check output.
2. Reproduce locally.
3. Apply the smallest fix.
4. Re-run the full validation set.
5. Commit and push the fix.
6. Wait for CI to pass.

Do not merge with failing checks.

## Failed Merge Recovery

If merge fails:

1. Stop immediately.
2. Confirm whether `main` changed.
3. Sync `main`.
4. Re-run baseline validation.
5. Recreate the branch from current `main` if needed.
6. Cherry-pick only the safe commit if the patch is still valid.

Safe reconstruction path:

powershell
git switch main
git fetch origin --prune
git pull --ff-only origin main
$branch = "governance/autonomous-recovery-$(Get-Date -Format yyyyMMdd-HHmmss)"
git switch -c $branch
git cherry-pick <commit>

Only continue if cherry-pick completes cleanly and validation passes.

## Post-Merge Recovery Verification

After a pull request is merged:

powershell
git switch main
git fetch origin --prune
git pull --ff-only origin main
python tools/governance_hardening_check.py
python tools/project_constitution_check.py
python -m pytest tests/test_governance_hardening_pack.py tests/test_project_constitution_pack.py tests/test_governance_bootstrap.py -q
git diff --check
git status --short
git log -1 --oneline

The repository is considered recovered only when:

- `main` is synchronized
- validation passes
- working tree is clean
- the expected merge commit is present
- obsolete branches are removed or pruned

## Branch Cleanup

After successful merge and synchronization:

powershell
git fetch origin --prune
git branch --merged main

Delete only confirmed obsolete local branches.

powershell
git branch -d <branch>

If the branch was already removed by pull request merge automation, a local deletion failure may be harmless when the branch no longer exists.

## Artifact Retention Requirements

Recovery must preserve:

- Commit history
- Pull request discussion
- CI results
- Validation output
- Governance documents
- Evidence branches when created
- Merge commit references
- Branch names used for review

Do not delete evidence branches until the recovery path is complete and reviewed.

## Autonomous Decision Rules

An autonomous agent may continue only when all of the following are true:

- Repository state is known.
- Current branch is intentional.
- Current diff is intentional.
- Baseline checks are green.
- No stop condition is active.
- The patch is small and reviewable.
- Commit message is specific.
- Push target is the expected branch.
- Pull request base is `main`.
- CI passes before merge.

## Recovery Completion Criteria

Recovery is complete when:

1. `main` is synchronized with `origin/main`.
2. Working tree is clean.
3. Full validation passes.
4. No unexpected branches remain active.
5. Failed branch state is preserved or safely discarded.
6. The next task starts from a fresh timestamped branch.