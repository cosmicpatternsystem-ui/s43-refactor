# Phase 18 Commercial RC Hardening Control Register - 2026-06-15

## Official State

Phase 18 is operating as Commercial Release Candidate Hardening.

The approved baseline is:

- Branch: phase17-work-from-restore
- Synchronization rule: laptop and GitHub must remain equal after every approved operation
- Sync path: tools/phase18_approved_sync_wrapper.ps1
- Feature policy: feature freeze
- Allowed work: Stability, Security, Test Coverage, Documentation/Audit, Release Readiness
- Forbidden work: new features, blind git add, manual unverified push, experimental baseline changes, undocumented critical file movement

## Current Hardening Decision

The first Phase 18 hardening action is not a product change.

The first action is to register the commercial RC control model so that all future technical hardening is:

- traceable
- gated
- reversible through Git history
- synchronized with GitHub
- limited to approved hardening categories
- compatible with one-copy/paste operational execution

## Required Gate For Every Future Phase 18 Operation

Every future operation must satisfy all of the following before it is considered official:

- Correct branch is active
- Working tree state is intentional
- Explicit file paths are provided
- Approved sync wrapper is used
- Quality gate passes
- Health check passes
- Push completes
- HEAD equals origin after fetch
- Working tree is clean after completion
- Result is documented when it affects release readiness

## Commercial Release Candidate Hardening Queue

### Priority 1 - Security

- Review secrets and credential exposure risks
- Confirm no operational command requires unsafe policy changes beyond process scope
- Confirm no archive or snapshot is treated as a replacement for Git history
- Confirm release artifacts do not contain unintended local-only data

### Priority 2 - Stability

- Preserve current passing quality gate
- Avoid large refactors
- Prefer small, isolated fixes
- Require explicit rollback path through Git history

### Priority 3 - Test Coverage

- Identify the highest-risk untested paths
- Add focused tests only when they reduce release risk
- Avoid broad test rewrites during RC hardening

### Priority 4 - Documentation And Audit

- Keep the roadmap, audit records, and release readiness checklist aligned
- Record operational decisions as dated audit artifacts
- Preserve one-copy/paste execution as the default operational standard

### Priority 5 - Release Readiness

- Prepare a release candidate checklist
- Verify branch, sync, quality, health, and audit state before any RC tag
- Do not tag or branch a release candidate until the hardening checklist is complete

## Immediate Next Action

The next technical action should be a read-only Phase 18 preflight audit script or report that checks repository sync, branch correctness, quality gate availability, health check availability, and release-readiness documentation presence.

No feature work is approved at this stage.
