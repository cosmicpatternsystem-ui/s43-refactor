# Repository Governance

## Objective

This document describes the repository governance baseline for maintainers and contributors.

It defines how changes should be proposed, reviewed, validated, and documented while preserving the repository's conservative automation posture.

## Governance Principles

Repository governance should remain:

- transparent
- reviewable
- evidence-based
- conservative with enforcement changes
- aligned with protected branch requirements
- documented before operational assumptions change

## Change Management

Most repository changes should flow through pull requests.

Pull requests should include:

- a clear summary
- scope of the change
- validation evidence
- risk notes when relevant
- confirmation of any enforcement impact
- links to related documentation or audit records when applicable

Direct changes to protected branches should be avoided unless explicitly required by repository policy or emergency response.

## Documentation-Only Changes

Documentation-only changes should not modify:

- `.github/workflows/*`
- `tools/*`
- repository rulesets
- branch protection settings
- required status checks
- release automation
- dependency policy
- package publishing behavior

If a documentation pull request reveals a needed automation or enforcement change, that change should be handled in a separate pull request.

## Automation Changes

Automation changes should be reviewed more carefully than ordinary documentation changes.

Automation-related pull requests should describe:

- workflow files changed
- scripts changed
- expected trigger behavior
- expected status check names
- whether the check is required or non-required
- rollback approach
- validation evidence

Automation changes should avoid renaming required checks unless the ruleset update is planned, reviewed, and coordinated.

## Ruleset and Branch Protection Changes

Ruleset or branch protection changes should use a dedicated governance pull request.

Such a pull request should include:

- reason for the change
- current required checks
- proposed required checks
- strict policy impact
- expected maintainer impact
- rollback plan
- validation plan

Ruleset changes should not be bundled with unrelated documentation, release, or feature work.

## Required Check Baseline

The current required protected-branch checks are:

- `hardening-tests`
- `policy-smokes`
- `Assert release readiness contract`

The current strict required status check policy is:

- `strict_required_status_checks_policy: false`

This document records the baseline but does not enforce it.

## Active Workflow Baseline

The current active workflows are:

- `Hardening Tests`
- `Operational Roadmap Gate`
- `Policy Smoke Tests`
- `PR Hygiene Gate`
- `Release Readiness Gate`
- `Dependency Graph`

Required workflows and non-required workflows are documented separately in the audit trail.

## Review Expectations

Maintainers should review pull requests for:

- correctness
- scope control
- validation evidence
- unexpected enforcement impact
- consistency with documented process
- compatibility with existing automation posture

For documentation-only work, reviewers should confirm that the change does not modify enforcement files or scripts.

## Evidence Expectations

Operationally significant pull requests should include evidence such as:

- local validation output
- pull request check results
- workflow status where relevant
- required-check baseline where relevant
- links to audit records where relevant

Evidence should be sufficient for a future maintainer to understand what changed and what did not change.

## Separation of Concerns

Governance expects separation between:

- documentation changes
- workflow changes
- script changes
- ruleset changes
- release process changes
- dependency policy changes
- feature implementation changes

Combining these areas increases review risk and should be avoided unless there is a clear reason.

## Emergency Changes

Emergency changes should still preserve traceability when possible.

If an emergency requires fast action:

1. Make the smallest safe change.
2. Record the reason.
3. Preserve logs and validation evidence.
4. Follow up with documentation or audit updates.
5. Restore normal pull request review as soon as possible.

## Out of Scope

This governance baseline does not add:

- new required checks
- new workflows
- new branch protection rules
- new release automation
- new dependency automation
- new contributor permission rules
- new publishing rules

## Related Documents

- `docs/RELEASE_PROCESS.md`
- `docs/RELEASE_RUNBOOK.md`
- `AUDIT/PHASE3_OPERATIONAL_INVENTORY.md`
- `AUDIT/PHASE3_AUTOMATION_CONTRACT_MAPPING.md`
- `AUDIT/PHASE3_OPERATIONAL_RUNBOOK.md`
- `AUDIT/PHASE4_RELEASE_CLOSURE_SNAPSHOT.md`

## Final Assessment

This governance baseline documents repository operating expectations while preserving the existing conservative enforcement posture.
