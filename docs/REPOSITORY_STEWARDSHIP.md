# Repository Stewardship

## Purpose

This document defines repository stewardship expectations for maintaining the
repository in a safe, understandable, auditable, and operationally consistent
state.

Repository stewardship focuses on responsible maintenance of documentation,
review expectations, evidence collection, continuity awareness, and preservation
of the existing enforcement model unless a separate explicit enforcement change
is proposed, reviewed, and approved.

## Scope

This document covers:

- documentation stewardship
- audit trail stewardship
- pull request review expectations
- operational continuity awareness
- maintenance documentation alignment
- evidence collection expectations
- drift awareness
- escalation boundaries
- enforcement change separation

This document does not modify repository enforcement.

## Stewardship Principles

Repository stewards should follow these principles:

1. Keep repository documentation accurate and understandable.
2. Preserve a clear audit trail for governance, maintenance, and continuity work.
3. Separate documentation-only changes from enforcement changes.
4. Avoid accidental modification of workflows, validation scripts, or automation.
5. Verify repository health signals before closing operational documentation work.
6. Record evidence when repository posture, expectations, or operational state are reviewed.
7. Escalate possible drift instead of silently normalizing it.

## Documentation Stewardship

Documentation updates should be made when:

- repository procedures change
- operational expectations become unclear
- evidence snapshots become outdated
- maintenance or continuity guidance needs clarification
- prior documentation no longer reflects repository practice

Documentation-only updates should avoid changes to:

- `.github/workflows/`
- `tools/`
- rulesets
- branch protection
- required status checks
- automation gate behavior

## Audit Trail Stewardship

Audit records should be used to preserve:

- phase objectives
- documentation artifacts added or updated
- validation expectations
- workflow visibility
- required check visibility
- enforcement boundary confirmations
- closure statements

Audit records should be concise, traceable, and aligned with the state of the
repository at the time they are created.

## Pull Request Stewardship

Documentation pull requests should:

- use an isolated branch
- describe documentation-only scope
- identify files changed
- confirm no enforcement impact
- run local validation where applicable
- allow existing repository checks to run unchanged
- merge only after expected checks complete successfully

## Repository Health Signals

Repository stewards should be aware of the following health signals:

- local `main` aligned with `origin/main`
- working tree clean before starting new work
- active workflow list visible
- required status checks unchanged unless intentionally modified
- strict required status checks policy unchanged unless intentionally modified
- recent commits traceable to reviewed pull requests

## Expected Active Workflow Baseline

The expected active workflow baseline remains:

- `Hardening Tests`
- `Operational Roadmap Gate`
- `Policy Smoke Tests`
- `PR Hygiene Gate`
- `Release Readiness Gate`
- `Dependency Graph`

## Expected Required Status Check Baseline

The expected required status check baseline remains:

- `hardening-tests`
- `policy-smokes`
- `Assert release readiness contract`

The expected strict required status checks policy remains:

- `strict_required_status_checks_policy: false`

## Enforcement Boundary

Repository stewardship documentation does not alter:

- repository rulesets
- branch protection
- required status checks
- workflow definitions
- validation scripts
- automation gate behavior
- merge enforcement behavior

Any future change to enforcement must be handled as a separate explicit change,
with clear intent, review, validation, and evidence.

## Drift Awareness

Potential drift includes:

- unexpected workflow changes
- unexpected required check changes
- unexpected ruleset or branch protection changes
- validation script changes outside an approved scope
- documentation no longer matching repository behavior
- automation behavior changing without audit evidence

When drift is suspected, stewards should record the observation and escalate
before introducing corrective changes.

## Escalation Expectations

Escalation is appropriate when:

- enforcement behavior appears different from documented expectations
- required checks differ from the recorded baseline
- workflows are unexpectedly added, removed, renamed, or disabled
- validation behavior changes without corresponding documentation
- repository health signals are inconsistent

Escalation should prioritize evidence collection before remediation.

## Final Statement

Repository stewardship is an ongoing documentation and review discipline. It
supports repository safety, continuity, and auditability while preserving the
existing enforcement model unless a separate explicit enforcement change is made.
