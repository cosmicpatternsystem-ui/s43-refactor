# Governance Runbook

## Purpose

This runbook documents the repository governance operating model.

It is documentation-only and does not modify enforcement.

## Governance Posture

The repository governance posture is intentionally conservative:

- governance changes are documented before enforcement changes are considered
- automation evidence is recorded through pull requests
- required checks remain limited to the established repository ruleset
- workflow and validation script changes are handled separately from documentation updates

## Current Required Checks

The repository ruleset currently requires:

- hardening-tests
- policy-smokes
- Assert release readiness contract

The current strict required status checks setting is expected to remain:

- strict_required_status_checks_policy: false

## Active Automation Workflows

The repository is expected to retain these active workflows:

- Hardening Tests
- Operational Roadmap Gate
- Policy Smoke Tests
- PR Hygiene Gate
- Release Readiness Gate
- Dependency Graph

## Governance Change Process

Use the following process for governance documentation updates:

1. Create a dedicated branch for the documentation update.
2. Keep the change documentation-only unless a separate enforcement phase is explicitly approved.
3. Run the local PR hygiene validation when available.
4. Open a pull request with clear summary, non-changes, and validation sections.
5. Wait for required and expected checks to complete successfully.
6. Merge only after checks are successful.
7. Confirm main branch state, active workflows, and required checks after merge.

## Enforcement Change Separation

Do not combine governance documentation updates with changes to:

- repository rulesets
- branch protection settings
- required status checks
- workflow files
- validation scripts
- application runtime code

Any enforcement change should be handled as a separate, explicitly scoped phase.

## Evidence Collection

For each governance phase, capture evidence for:

- pull request number and URL
- successful check results
- latest main branch commit after merge
- active workflow list
- required status check list
- strict required status checks setting

## Recovery Guidance

If a governance PR check fails:

1. Do not merge the PR.
2. Review the failing check output.
3. Confirm the change is documentation-only.
4. Fix only the documentation issue unless a broader scope is explicitly approved.
5. Re-run the PR checks before merge.

If a ruleset or required check appears changed unexpectedly:

1. Stop the phase.
2. Capture the observed ruleset output.
3. Do not attempt to revert unrelated settings without explicit approval.
4. Compare against the last recorded governance evidence snapshot.
5. Decide the next action in a separate review step.

## Closure Criteria

A governance documentation phase is complete when:

- the documentation PR is merged to main
- main is aligned with origin/main
- working tree is clean
- workflows remain active
- required checks remain unchanged
- strict required status checks setting remains unchanged
