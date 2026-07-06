# Autonomous Governance Operations Index

## Purpose

This index defines the canonical operating route for autonomous governance activity in this repository.

It connects the autonomous governance documents into a single decision path so an operator, automation agent, or reviewer can determine which control document applies before taking action.

## Operating Model

Autonomous governance work must proceed from the repository state, the active task, and the available evidence.

The operator or automation agent must identify the current operating condition before selecting a runbook or checklist.

The index is a routing document. It does not replace the underlying control documents.

## Primary Documents

Use these documents as the primary autonomous governance controls:

- `docs/governance/AUTONOMOUS_FAILURE_HANDLING_RUNBOOK.md`
- `docs/governance/AUTONOMOUS_RECOVERY_AND_ROLLBACK_RUNBOOK.md`
- `docs/governance/AUTONOMOUS_MERGE_SAFETY_CHECKLIST.md`

## Decision Routing

Use the following routing rules before changing repository state.

| Condition | Primary control |
| --- | --- |
| A validation, workflow, merge, branch, push, or evidence step fails | `AUTONOMOUS_FAILURE_HANDLING_RUNBOOK.md` |
| A completed or partially completed change must be unwound, isolated, or restored | `AUTONOMOUS_RECOVERY_AND_ROLLBACK_RUNBOOK.md` |
| A change is ready for pull request review, merge, or post-merge verification | `AUTONOMOUS_MERGE_SAFETY_CHECKLIST.md` |
| The correct control is unclear | Stop and classify the operating condition before continuing |

## Standard Operating Sequence

Use this sequence for normal autonomous governance changes:

1. Sync `main` from `origin/main`.
2. Confirm the worktree is clean.
3. Create a task-specific branch from current `main`.
4. Run baseline validation before editing.
5. Make the smallest complete change that satisfies the task.
6. Run the required validation set after editing.
7. Confirm `git diff --check` is clean.
8. Commit only the intended files.
9. Push the branch and open a pull request.
10. Wait for all required checks to complete.
11. Apply the merge safety checklist before merge.
12. Merge only after local and remote evidence agree.
13. Sync `main` after merge.
14. Run post-merge validation on `main`.

## Failure Routing

If any required step fails, stop normal execution and use:

`docs/governance/AUTONOMOUS_FAILURE_HANDLING_RUNBOOK.md`

Failure handling applies to:

- dirty worktree state that cannot be explained
- validation failure
- test failure
- encoding or line-ending failure
- push failure
- pull request check failure
- merge failure
- missing or contradictory evidence

Do not continue the normal operating sequence until the failure is classified and resolved.

## Recovery Routing

If repository state must be restored, isolated, or unwound, use:

`docs/governance/AUTONOMOUS_RECOVERY_AND_ROLLBACK_RUNBOOK.md`

Recovery and rollback handling applies to:

- incorrect branch base
- accidental file inclusion
- incorrect commit content
- failed merge attempt
- incomplete change that must be abandoned
- local state that must be preserved before correction
- post-merge issue requiring a controlled follow-up

Prefer forward corrective commits for published history unless the recovery runbook explicitly allows another path.

## Merge Routing

Before merging any autonomous governance pull request, use:

`docs/governance/AUTONOMOUS_MERGE_SAFETY_CHECKLIST.md`

Merge safety applies after the change has been committed, pushed, reviewed, and validated.

The merge decision must confirm:

- branch base is current enough for the change
- local validation is green
- remote checks are green
- pull request content matches the intended scope
- no unrelated files are included
- post-merge validation is planned

## Evidence Routing

Autonomous governance actions must leave enough evidence for future operators to reconstruct the decision.

Minimum evidence includes:

- branch name
- base commit
- changed files
- validation commands
- validation results
- pull request number when applicable
- merge commit when applicable
- post-merge validation result when applicable

Evidence should be recorded in the pull request, command output, commit history, or follow-up governance notes.

## Stop Conditions

Stop and do not continue autonomous execution when:

- the active branch cannot be identified
- the base commit is uncertain
- local and remote repository state disagree
- validation results are missing or contradictory
- a command would rewrite published history without explicit approval
- the intended changed files do not match the actual diff
- a merge condition is ambiguous
- required evidence cannot be produced

When a stop condition is reached, classify the condition and route to the failure or recovery runbook.

## Maintenance Rules

This index must remain small and operational.

Update it only when:

- a new autonomous governance control document is added
- an existing control document is renamed
- routing rules change
- required validation or evidence expectations change

Do not duplicate full runbook content in this index. Keep detailed procedures in the primary control documents.
## Governance Manifest

- `docs/governance/GOVERNANCE_DOCUMENTS_MANIFEST.md`
## Strategic Control Plane

- `docs/strategy/STRATEGIC_CONTROL_PLANE.md`
- `docs/strategy/TOP_LEVEL_COMMERCIAL_OPERATING_DOCTRINE.md` - canonical commercial doctrine for revenue quality, pricing discipline, market positioning, customer-fit control, and durable institutional trust