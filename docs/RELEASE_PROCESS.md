# Release Process

## Objective

This document defines the baseline release process for this repository.

The goal is to provide a clear, auditable, and conservative release documentation baseline without introducing new automation enforcement.

## Release Philosophy

Releases should be:

- reviewable
- reproducible
- aligned with repository automation contracts
- traceable to approved changes on `main`
- validated before publication

This repository currently favors conservative enforcement. Release documentation should describe the expected process without expanding branch protection or required status checks unless explicitly approved in a future phase.

## Release Readiness Definition

A release candidate is considered ready for release when:

1. The release change is based on the latest `main`.
2. Required protected-branch checks have passed.
3. The release readiness contract is satisfied.
4. No unexpected workflow failures are present.
5. The intended release contents are documented and reviewable.
6. The repository state is clean and traceable.

## Current Required Checks

The active required protected-branch checks are:

- `hardening-tests`
- `policy-smokes`
- `Assert release readiness contract`

These checks represent the current enforced release baseline.

## Current Non-Required Automation

The following automation may provide additional signal but is not currently required for merge:

- `Assert operational roadmap contract`
- `Assert PR hygiene contract`
- `Dependency Graph`

These checks should be reviewed when relevant, but they do not currently block release activity through branch protection.

## Pre-Release Verification

Before preparing a release, maintainers should verify:
```bash
git checkout main
git pull --ff-only origin main
git status -sb
git log --oneline -10

Maintainers should also inspect workflow availability:

bash
gh workflow list

And inspect the active required status check configuration:

bash
gh api repos/cosmicpatternsystem-ui/s43-refactor/rulesets/17888945 \
  --jq '.rules[]? | select(.type=="required_status_checks")'

## Pull Request Expectations for Release Changes

Release-related pull requests should include:

- a clear summary of the release intent
- validation evidence
- confirmation that required checks passed
- any relevant operational notes
- confirmation that no unintended enforcement changes were introduced

## Release Readiness Gate

The repository includes an active workflow named:

- `Release Readiness Gate`

The required check associated with this release baseline is:

- `Assert release readiness contract`

This check is part of the current protected-branch enforcement set.

## Enforcement Policy

This document does not change enforcement.

Any future change to release enforcement must be handled through a dedicated pull request and should include:

- explicit rationale
- before/after required-check comparison
- ruleset impact assessment
- rollback plan
- maintainer approval

## Out of Scope

This baseline does not introduce:

- automated release publishing
- tag creation automation
- changelog generation automation
- artifact publishing automation
- package registry publishing
- additional required checks

## Final Assessment

This document establishes the baseline release process for the repository.

It is documentation-only and preserves the existing conservative automation posture.
