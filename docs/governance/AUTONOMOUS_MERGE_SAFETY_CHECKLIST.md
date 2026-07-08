# Autonomous Merge Safety Checklist

This checklist defines the minimum safety gates for autonomous merge operations.

It is intended to keep merge decisions deterministic, reviewable, auditable, and
recoverable. It complements the autonomous follow-up checklist, failure handling
runbook, and recovery and rollback runbook.

## Purpose

Autonomous merge work must preserve repository integrity before, during, and
after every pull request lifecycle.

This checklist exists to ensure that every merge:

- Starts from a synchronized and validated base.
- Uses a narrow, reviewable branch.
- Produces a minimal and intentional diff.
- Passes local validation before publication.
- Passes remote checks before merge.
- Leaves `main` synchronized and clean after merge.
- Retains enough evidence to support audit and recovery.

## Scope

This checklist applies to autonomous or semi-autonomous changes that use:

- Timestamped working branches.
- GitHub pull requests.
- Squash merges.
- Branch deletion after successful merge.
- Local post-merge synchronization.
- Governance validation before and after integration.

## Non-Goals

This checklist does not replace:

- Human review where required.
- Security review for sensitive changes.
- Release approval gates.
- Incident response procedures.
- Rollback procedures.

If a change requires any of those controls, this checklist must be treated as a
minimum baseline rather than a complete approval process.

## Pre-Branch Safety

Before creating a working branch, verify that the local repository is clean and
synchronized.

Required checks:
```bash
git fetch origin --prune
git switch main
git pull --ff-only origin main
git status --short
git log -1 --oneline
git diff --check

Expected state:

- Current branch is `main`.
- `main` is up to date with `origin/main`.
- `git status --short` has no output.
- `git diff --check` has no output.
- The latest commit is known and recorded in the working notes.

Stop if:

- The working tree is dirty.
- `main` cannot fast-forward.
- There are untracked files that are not part of the intended task.
- The latest commit is not the expected base.
- Fetch or pull reports repository state that cannot be explained.

## Branch Safety

Each autonomous task must use a dedicated timestamped branch.

Recommended branch format:

text
governance/<topic>-YYYYMMDD-HHMMSS

Example:

text
governance/autonomous-next-20260706-120430

Required branch actions:

bash
git switch -c <branch>
git push -u origin <branch>
git branch --show-current
git status --short
git log -1 --oneline

Expected state:

- The new branch tracks its remote counterpart.
- The branch starts from the current `main`.
- The working tree remains clean immediately after branch creation.

Stop if:

- The branch was created from an unexpected base.
- The branch name is ambiguous or reused.
- The remote push fails.
- Tracking is not established.

## Baseline Validation

Before editing files, run baseline validation on the working branch.

Required checks:

bash
python tools/governance_hardening_check.py
python tools/project_constitution_check.py
python -m pytest tests/test_governance_hardening_pack.py tests/test_project_constitution_pack.py tests/test_governance_bootstrap.py -q
git diff --check
git status --short

Expected state:

- Governance hardening check passes.
- Project constitution check passes.
- Governance pytest suite passes.
- No whitespace errors exist.
- Working tree is clean.

Stop if:

- Any validation fails.
- The failure is unrelated to the intended change and cannot be explained.
- The working tree changes during baseline validation.
- Test output indicates flaky or nondeterministic behavior.

## Patch Size Safety

Autonomous merge candidates should be small and reviewable.

Preferred patch properties:

- One conceptual change per pull request.
- Minimal file count.
- Minimal generated noise.
- No unrelated formatting churn.
- No mixed policy and implementation changes unless explicitly required.
- No drive-by edits.

For documentation patches:

- Use UTF-8 without BOM.
- Use LF line endings.
- Keep headings stable and descriptive.
- Avoid environment-specific claims unless they are operationally required.
- Avoid references that cannot be validated from repository content.

Stop if:

- The patch expands beyond the intended scope.
- The diff contains unrelated files.
- Formatting changes obscure the actual change.
- Generated files appear unexpectedly.
- Sensitive data or local-only paths are introduced.

## Encoding and Line Ending Safety

New text files must be written with durable repository-safe encoding.

Required properties:

- UTF-8 without BOM.
- LF line endings.
- No trailing whitespace.
- No hidden editor metadata.

PowerShell-safe write pattern:

powershell
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($path, $content.Replace("`r`n", "`n"), $utf8NoBom)

Required verification:

bash
git diff --check

Stop if:

- `git diff --check` reports whitespace errors.
- A file is written with unexpected CRLF churn.
- A file contains BOM where BOM-free UTF-8 is expected.

## Pre-Commit Safety

Before committing, inspect the exact diff.

Required checks:

bash
git status --short
git diff --stat
git diff -- <changed-files>
git diff --check

Expected state:

- Only intended files are modified or added.
- Diff content matches the task.
- No whitespace errors exist.
- No unrelated local files are staged.

Stop if:

- The diff contains unexpected files.
- The diff includes secrets, credentials, tokens, or local machine artifacts.
- The diff includes temporary files.
- The diff cannot be explained simply.

## Commit Safety

Stage only intended files.

Required actions:

bash
git add <intended-files>
git diff --cached --stat
git diff --cached --check
git status --short
git commit -m "<clear imperative commit message>"

Commit message requirements:

- Imperative mood.
- Short and specific.
- Matches the actual patch.
- Does not claim more than the patch delivers.

Examples:

text
Add autonomous merge safety checklist
Add autonomous failure handling runbook
Add autonomous recovery and rollback runbook

Stop if:

- Staged files differ from intended files.
- The cached diff has whitespace errors.
- The commit message is vague or inaccurate.
- Commit hooks fail.

## Pre-Push Safety

After commit and before push, verify the branch state.

Required checks:

bash
git status --short
git log -1 --oneline
git diff origin/main...HEAD --stat
git diff origin/main...HEAD --check

Expected state:

- Working tree is clean.
- The latest commit is the intended commit.
- The branch diff contains only intended changes.
- No whitespace errors exist across the branch diff.

Stop if:

- The branch contains multiple unintended commits.
- The diff includes unrelated changes.
- The working tree is dirty after commit.
- The branch has diverged unexpectedly.

## Pull Request Safety

Create a pull request only after local validation passes.

Recommended command:

bash
gh pr create --base main --head <branch> --title "<title>" --body "<body>"

PR body should include:

- Summary of the change.
- Validation commands and results.
- Risk level.
- Rollback note.
- Confirmation that the working tree was clean before push.

Minimum PR body structure:

text
## Summary

- ...

## Validation

- `python tools/governance_hardening_check.py`
- `python tools/project_constitution_check.py`
- `python -m pytest ... -q`
- `git diff --check`

## Risk

Low. Documentation/governance-only change.

## Rollback

Revert the squash merge commit if needed.

Stop if:

- The PR title does not match the patch.
- The PR body omits validation evidence.
- The PR diff differs from the local expected diff.
- GitHub reports unexpected changed files.

## Remote Check Safety

Before merge, remote checks must be inspected.

Required command:

bash
gh pr checks <pr-number>

Expected state:

- Required checks are successful.
- No required check is pending.
- No required check is skipped unexpectedly.
- No failing check is ignored.

Stop if:

- Any required check fails.
- Any required check remains pending beyond normal runtime.
- Check names differ unexpectedly.
- The PR receives new commits after checks were reviewed.
- GitHub reports merge conflicts.

## Merge Safety

Use squash merge for autonomous governance patches unless another merge method is
explicitly required.

Recommended command:

bash
gh pr merge <pr-number> --squash --delete-branch

Expected state:

- PR is merged into `main`.
- Remote branch is deleted.
- The resulting commit message is accurate.
- The merge commit or squash commit hash is recorded.

Stop if:

- GitHub refuses the merge.
- Checks are not green.
- Branch deletion fails in a way that cannot be explained.
- The merge target is not `main`.
- The PR has changed since the final review.

## Post-Merge Safety

After merge, return local `main` to the authoritative remote state.

Required commands:

bash
git fetch origin --prune
git switch main
git pull --ff-only origin main
git status --short
git log -1 --oneline

Expected state:

- Current branch is `main`.
- Local `main` matches `origin/main`.
- Working tree is clean.
- Latest commit is the merged squash commit.
- Deleted remote branches are pruned.

Stop if:

- `main` cannot fast-forward.
- The latest commit is not the expected merge result.
- The working tree is dirty.
- Remote branch deletion did not complete and requires manual cleanup.

## Post-Merge Validation

Run final validation on `main`.

Required checks:

bash
python tools/governance_hardening_check.py
python tools/project_constitution_check.py
python -m pytest tests/test_governance_hardening_pack.py tests/test_project_constitution_pack.py tests/test_governance_bootstrap.py -q
git diff --check
git status --short

Expected state:

- All governance checks pass.
- Tests pass.
- Whitespace check is clean.
- Working tree is clean.

Stop if:

- Validation fails on `main`.
- The failure was not present before merge.
- The failure indicates repository policy drift.
- The working tree changes during validation.

## Evidence Retention

For each autonomous merge, retain the following in working notes or PR metadata:

- Branch name.
- Base commit.
- Commit hash before PR.
- PR number.
- Remote check result.
- Merge method.
- Final squash or merge commit hash.
- Post-merge validation result.
- Final `git status --short` result.

Minimum final state record:

text
main clean and synchronized at <commit>
PR #<number> merged successfully
Local validation: OK
Remote checks: successful
Working tree: clean

## Recovery Linkage

If a merge introduces failure after integration:

1. Stop further autonomous changes.
2. Preserve logs and command output.
3. Identify the merge commit.
4. Follow the autonomous recovery and rollback runbook.
5. Prefer revert over history rewrite for shared branches.
6. Re-run post-recovery validation on `main`.

Do not stack additional fixes on top of a failed merge unless the recovery
runbook explicitly allows it.

## Final Merge Readiness Gate

A PR is ready to merge only when all of the following are true:

- The branch was created from synchronized `main`.
- Baseline validation passed before edits.
- The patch is narrow and intentional.
- Local validation passed after edits.
- The committed diff contains only intended files.
- The PR body includes validation evidence.
- Remote checks are successful.
- The PR has no unresolved conflicts.
- The merge target is `main`.
- Rollback path is known.
- Post-merge validation plan is known.

If any item is false or unknown, the merge is not ready.