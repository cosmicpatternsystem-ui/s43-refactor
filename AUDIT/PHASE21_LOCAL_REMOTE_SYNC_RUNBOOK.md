# Phase 21 Local Remote Sync Runbook

Status: DRAFT FOR AUDIT REVIEW
Phase: 21
Scope: Non-destructive local and remote repository synchronization practices
Production Release: BLOCKED WITHOUT APPROVAL
Destructive Automation: BLOCKED
Secrets Handling: DO NOT STORE OR PRINT SECRETS

## Purpose

This runbook defines how operators and automation should assess local and remote repository synchronization before audit closure, release dry-runs, or future production workflows. It is intentionally non-destructive and does not authorize fetch, pull, push, reset, checkout, clean, delete, tag, merge, or commit actions.

## Safety Boundary

This runbook allows read-only inspection commands and local audit reporting. If synchronization requires a state-changing command, stop and request explicit operator approval outside this runbook.

Forbidden by this runbook:

- `git add`
- `git commit`
- `git push`
- `git pull`
- `git fetch` unless separately approved
- `git reset`
- `git checkout`
- `git clean`
- branch deletion
- tag creation or deletion
- file deletion

## Definitions

- Clean working tree: `git status --short` produces no output.
- Dirty working tree: tracked or untracked files are present in `git status --short`.
- Upstream: the branch configured as `@{upstream}` for the current branch.
- Behind: upstream has commits not present locally.
- Ahead: local branch has commits not present upstream.
- Divergent: both ahead and behind counts are non-zero.
- Remote fetch state: the local remote-tracking ref that represents the last known upstream state.

## Required Read-Only Checks

Run these checks before claiming sync readiness:

```text
pwd
git branch --show-current
git rev-parse --is-inside-work-tree
git rev-parse --abbrev-ref --symbolic-full-name @{upstream}
git status --short
git status --branch --short
git rev-list --left-right --count HEAD...@{upstream}
git for-each-ref --format=%(refname:short) %(objectname:short) %(committerdate:iso8601) refs/remotes
git status
```

The Phase 21 helper may be used when present:

```text
python3 tools/ai/verify_repo_sync.py
```

For local artifact drafting only, operators may document an allowed dry-run condition:

```text
python3 tools/ai/verify_repo_sync.py --allow-dirty --allow-ahead
```

This dry-run allowance does not mean the repository is release-ready or commit-ready.

## Pass Criteria

Repository sync is safe for release-oriented review only when all of the following are true:

1. Current directory is inside the intended Git repository.
2. Current branch is the expected branch.
3. Upstream branch is configured.
4. Remote-tracking ref exists locally.
5. Working tree is clean.
6. Ahead count is zero.
7. Behind count is zero.
8. Divergence is false.
9. Remote metadata is present and recent enough for the workflow.
10. No unexpected untracked paths exist.

## Fail Conditions

Stop and report failure if any of the following are true:

1. Not inside a Git work tree.
2. Current branch is detached or unexpected.
3. Upstream is missing.
4. Remote-tracking ref is missing.
5. Working tree is dirty and not explicitly allowed for local dry-run review.
6. Behind count is greater than zero.
7. Ahead count is greater than zero and not explicitly allowed for local dry-run review.
8. Ahead and behind are both greater than zero.
9. Remote metadata cannot be inspected.
10. Command output is ambiguous or incomplete.

## Dirty Tree Handling

If `git status --short` lists files:

1. Do not delete or reset files.
2. Inspect untracked files before editing them.
3. Confirm whether the paths match the approved work scope.
4. Record the dirty state in the final handoff.
5. Do not claim commit readiness until the operator approves staging and commit actions.

Phase 21 approved local drafting scope is limited to:

- `AUDIT/PHASE21_*.md`
- `tools/ai/verify_repo_sync.py`
- Previously inspected `AI_AUDIT/` advisory outputs
- Previously inspected `tools/ai/` supervisor tooling

## Behind State Handling

If the branch is behind upstream:

1. Stop release, closure, or production-impacting work.
2. Report the behind count.
3. Do not run `git pull` automatically.
4. Ask the operator to approve the preferred sync method.
5. Re-run preflight after synchronization.

## Ahead State Handling

If the branch is ahead of upstream:

1. Stop release readiness claims.
2. Report the ahead count.
3. Do not push automatically.
4. Confirm whether the ahead commits are expected.
5. Require approval before push, pull request, or commit-related operations.

For local dry-run artifact drafting, ahead state may be documented as allowed only when no external mutation occurs.

## Divergence Handling

If ahead and behind counts are both greater than zero:

1. Stop immediately.
2. Preserve current evidence.
3. Do not merge, rebase, reset, checkout, or pull automatically.
4. Escalate to a human repository steward.
5. Resume only after explicit recovery instructions.

## Remote Fetch State Handling

The sync verifier inspects local remote-tracking refs. It does not fetch. If remote state appears stale or unavailable:

1. Treat the result as unsafe for release readiness.
2. Ask the operator whether a fetch is approved.
3. Record the last known remote-tracking commit and timestamp when available.
4. Re-run sync verification after any approved fetch.

## Audit Handoff Format

A sync handoff should include:

```text
Repository: <path>
Branch: <branch>
Commit: <short sha>
Upstream: <upstream>
Working tree: clean|dirty
Ahead: <count>
Behind: <count>
Divergent: yes|no
Remote tracking ref: present|missing
Allowed dry-run exceptions: none|dirty|ahead
Result: PASS|FAIL
Stop condition: <condition or none>
Files created or modified: <paths>
```

## Phase 21 Expected State

During Phase 21 artifact drafting, `git status --short` is expected to show untracked Phase 21 artifacts until the operator approves staging and commit. This is not commit-ready by itself. Commit readiness requires all requested files to exist, validation to pass, and the operator to approve `git add` and `git commit` later.

## Final Rule

Never fix synchronization risk by running a destructive or remote-mutating command automatically. Detect, report, and wait for approval.
