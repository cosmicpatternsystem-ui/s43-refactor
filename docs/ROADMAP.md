# Project Roadmap

This file records durable project direction and phase status for future work.

## Current Durable Milestone

### Phase 12: Governance Risk Guard Input Validation

Status: completed and pushed.

Branch:
- phase12-governance-design

Code milestone tag:
- phase12-risk-guard-input-validation

Latest confirmed commits:
- 1881a81 fix(governance): align invalid context severity with decision contract
- 183c929 test(governance): harden invalid context handling

Validation:
- python -m pytest tests/test_risk_guard_input_validation.py
- python -m pytest

Last confirmed result:
- 53 passed
- 2 skipped

## Professional Decision

Phase 12 governance input-validation hardening is considered implementation-complete.
The branch is ready for PR review and squash merge when appropriate.

Do not rewrite the pushed commits unless there is a specific release-management reason.
Use PR review as the final merge gate.

## Next Recommended Phases

### Phase 12 Follow-up: Governance Observability

Goal:
- Add durable reporting around governance decisions without changing decision semantics.

Possible work:
- summarize blocked/allowed decisions
- expose risk guard decision metadata in status/reporting paths
- add tests for governance reporting consistency

### Phase 13: Guard v2 Planning

Goal:
- design the next governance guard layer without disrupting the stable Phase 12 contract.

Principles:
- keep GovernanceDecision contract stable
- add new rules incrementally
- prefer explicit rule IDs
- maintain dry-run compatibility
- preserve auditability through tests and docs

## Merge Guidance

Preferred strategy:
- Open PR from phase12-governance-design
- Review the two implementation commits
- Use squash merge into the target branch if a clean main history is desired

Suggested squash title:
- feat(governance): finalize phase12 risk guard input validation hardening
