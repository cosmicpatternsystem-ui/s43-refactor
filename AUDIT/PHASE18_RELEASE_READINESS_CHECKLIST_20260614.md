# Phase 18 Release Readiness Checklist - 2026-06-14

## Release Candidate Gate

A release candidate baseline must not be declared until every mandatory item is complete.

## Mandatory Checks

- Official branch is phase17-work-from-restore
- Working tree is validated before approved sync
- Quality gate passes
- Health check passes
- Approved sync passes
- GitHub push is performed only by approved sync automation
- HEAD equals origin/phase17-work-from-restore after sync
- No unreviewed files are staged
- No blind git add . is used
- No feature development is included in the release candidate hardening baseline
- Success marker is printed only after real post-sync verification

## Documentation Checks

- Commercial roadmap exists and is current
- Phase 18 plan exists and is current
- Operational baseline exists and is current
- Archive manifest exists and is current
- Release readiness checklist exists and is current
- Risk register exists and is current
- One-copy-paste automation standard exists and is current
- Opening automation verification exists and is current

## Stability Checks

- Startup path is documented
- Health check mode is documented
- Snapshot behavior is documented
- Critical scripts are present
- Failure modes are captured in risk register
- Rollback path is documented before tagging

## Security Checks

- No secrets are committed
- No credentials are added to audit files
- No local machine-only secrets are added to repository files
- No unsafe manual deployment step is introduced
- No unapproved remote is used
- No manual push bypass is used

## Release Candidate Decision

A release candidate can be tagged only after:

- All mandatory checks pass
- Open critical risks are either resolved or explicitly accepted
- Approved sync completes successfully
- Laptop and GitHub are verified equal
- Final verification is recorded
