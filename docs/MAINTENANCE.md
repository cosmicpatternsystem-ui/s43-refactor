# Repository Maintenance

This document defines the maintenance baseline for this repository.

It is documentation-only and does not change automation, rulesets, branch protection,
required checks, workflow files, or validation scripts.

## Objective

The objective of repository maintenance is to keep the project understandable,
reviewable, auditable, and safe to operate over time.

Maintenance work should preserve the current enforcement model unless a future,
explicitly approved change updates that model through a dedicated governance path.

## Maintenance Principles

Repository maintenance follows these principles:

- Keep documentation current with the actual repository state.
- Keep operational expectations explicit and reviewable.
- Preserve separation between documentation, automation, and enforcement.
- Avoid accidental expansion of required checks or protected branch behavior.
- Record evidence when repository governance, release, or maintenance posture changes.
- Prefer small, reviewable pull requests with clear scope.

## Maintenance Scope

Maintenance may include:

- Updating repository documentation.
- Refreshing audit snapshots.
- Recording current workflow and required check evidence.
- Clarifying owner, reviewer, and maintainer expectations.
- Documenting known operational procedures.
- Identifying future improvements without implementing them immediately.

Maintenance does not imply automation or enforcement changes.

## Documentation Maintenance

Documentation should be reviewed when any of the following changes occur:

- Release process expectations change.
- Governance expectations change.
- Required checks change.
- Active workflows change.
- Repository ownership or review expectations change.
- Maintenance procedures are clarified or corrected.

Documentation updates should identify whether they are descriptive only or whether
they correspond to an actual behavior change.

## Audit Trail Maintenance

Audit documents should be used to preserve important repository state transitions.

Audit snapshots may record:

- The current mainline commit.
- The active workflow baseline.
- The required status check baseline.
- The relationship to prior phases.
- Confirmation that no enforcement change occurred.
- Any known validation expectations.

Audit files should remain descriptive. They should not create new automation
requirements by themselves.

## Workflow Baseline Awareness

At the time this maintenance baseline is documented, the known active workflow set is:

- Hardening Tests
- Operational Roadmap Gate
- Policy Smoke Tests
- PR Hygiene Gate
- Release Readiness Gate
- Dependency Graph

This document does not require, remove, rename, or modify any workflow.

## Required Check Baseline Awareness

At the time this maintenance baseline is documented, the known required status checks are:

- hardening-tests
- policy-smokes
- Assert release readiness contract

The known strict required status checks policy is:

- strict_required_status_checks_policy: false

This document does not change the required check set or enforcement policy.

## Maintenance Review Expectations

Maintenance pull requests should be reviewed for:

- Scope clarity.
- Documentation-only boundaries when applicable.
- Consistency with governance and release documentation.
- Evidence that required checks and workflows were not changed unintentionally.
- Clear relationship to prior audit snapshots.

## Cadence Expectations

There is no automated maintenance cadence introduced by this document.

Maintainers may choose to review maintenance documentation periodically or after
meaningful repository changes. Any formal cadence should be introduced through a
future governance-approved documentation or process update.

## Owner Expectations

Maintainers are expected to:

- Keep repository documentation understandable.
- Avoid mixing documentation updates with unrelated automation changes.
- Confirm required checks before and after governance-sensitive changes.
- Preserve audit continuity across major documentation phases.
- Escalate enforcement changes into explicit governance review.

## Enforcement Change Policy

Any future change to rulesets, branch protection, required checks, workflow files,
or validation scripts must be handled separately from documentation-only maintenance.

Such a change should include:

- A clear objective.
- A dedicated pull request.
- Explicit review of enforcement impact.
- Before-and-after evidence.
- Validation of resulting repository behavior.

## Related Documents

Related repository documents include:

- `docs/GOVERNANCE.md`
- `docs/RELEASE_PROCESS.md`
- `docs/RELEASE_RUNBOOK.md`
- `AUDIT/PHASE4_RELEASE_CLOSURE_SNAPSHOT.md`
- `AUDIT/PHASE5_GOVERNANCE_CLOSURE_SNAPSHOT.md`
