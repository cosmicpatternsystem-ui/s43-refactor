# Maintenance Runbook

This document defines the operational maintenance runbook for the repository.

The purpose of this runbook is to provide maintainers with a repeatable,
documentation-only procedure for observing repository health, collecting evidence,
reviewing drift, and escalating governance-sensitive changes.

This document does not change repository enforcement.

## Scope

This runbook covers:

- routine maintenance review
- evidence collection
- workflow visibility checks
- required status check visibility
- documentation drift review
- escalation expectations
- closure criteria for maintenance cycles

This runbook does not authorize direct changes to:

- GitHub rulesets
- branch protection
- required status checks
- workflow files
- validation scripts
- enforcement policy

Any such change must be handled as a separate governance-controlled change.

## Maintenance Principles

Repository maintenance should follow these principles:

1. Prefer observation before modification.
2. Record evidence before and after any maintenance activity.
3. Keep documentation changes separate from enforcement changes.
4. Avoid bundling unrelated repository changes.
5. Preserve the existing automation and protection baseline unless an explicit
   governance-approved change requires otherwise.

## Routine Maintenance Checklist

Maintainers should periodically confirm the following:

- the local `main` branch is aligned with `origin/main`
- the working tree is clean
- recent documentation commits are visible in history
- active workflows remain visible
- required status checks remain unchanged
- no unexpected enforcement drift has occurred

Suggested commands:
```bash
git checkout main
git pull --ff-only origin main
git status -sb
git log --oneline -10
gh workflow list
gh api repos/cosmicpatternsystem-ui/s43-refactor/rulesets/17888945 --jq '.rules[]? | select(.type=="required_status_checks")'

## Evidence Collection

A maintenance evidence snapshot should include:

- current branch status
- recent commit history
- active workflow list
- required status check configuration
- confirmation that no workflow files were changed
- confirmation that no validation scripts were changed
- confirmation that ruleset and branch protection were not modified

Evidence should be stored in `AUDIT/` when a maintenance phase or review cycle is
completed.

## Documentation Review

Maintenance documentation should be reviewed for:

- outdated references
- stale process descriptions
- missing escalation instructions
- inconsistent terminology
- incomplete closure criteria
- unclear distinction between documentation and enforcement

Documentation updates should remain narrow and traceable.

## Drift Review

Potential drift indicators include:

- new or removed workflow names
- renamed required checks
- changed required check count
- changed strict required status check policy
- unexpected changes in validation scripts
- unexpected changes in enforcement documentation
- unreviewed automation behavior changes

If drift is detected, maintainers should not immediately modify enforcement.
Instead, they should record evidence and escalate for governance review.

## Escalation Path

Escalation is required when a proposed change affects:

- repository rulesets
- branch protection
- required checks
- workflow definitions
- validation scripts
- release gates
- PR hygiene gates
- hardening gates
- policy smoke tests

Escalated changes should be isolated from documentation-only changes.

## Maintenance Pull Request Expectations

Maintenance pull requests should:

- use a focused branch
- include documentation-only changes
- pass local hygiene validation where applicable
- avoid workflow and tool changes
- include clear PR summary and test/evidence notes
- wait for required checks to complete before merge

## Closure Criteria

A maintenance cycle may be considered complete when:

- documentation updates are merged
- required checks have passed
- `main` is aligned with `origin/main`
- active workflow list is unchanged unless separately approved
- required status checks are unchanged unless separately approved
- final evidence is recorded
- no enforcement drift is introduced

## Out of Scope

The following are out of scope for this runbook:

- changing branch protection
- editing rulesets
- adding or removing required checks
- editing workflow files
- editing validation scripts
- changing security policy
- changing release enforcement behavior
