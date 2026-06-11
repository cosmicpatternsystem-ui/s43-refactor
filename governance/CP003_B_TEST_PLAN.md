# CP003-B Test Plan

## Status

- Phase: CP003-B
- Document type: Test Plan
- Branch: cp003-b-integration-planning
- Base lock tag: s43-cp003-a-locked
- Charter tag: s43-cp003-b-charter-v1
- Insertion Map tag: s43-cp003-b-insertion-map-v1
- Impact Assessment tag: s43-cp003-b-impact-assessment-v1
- Safety Gate Review tag: s43-cp003-b-safety-gate-review-v1
- Rollback Plan tag: s43-cp003-b-rollback-plan-v1
- Runtime integration: UNAUTHORIZED
- Live trading: UNAUTHORIZED
- Baseline executable mutation: UNAUTHORIZED

## Purpose

This document defines the minimum test strategy required before any future executable CP003 integration proposal.

This document is planning-only.

It does not authorize code mutation, runtime integration, live trading, broker connectivity, or environment activation.

## Test Governance Rule

No future CP003 executable mutation may be proposed unless a specific test procedure exists for that mutation.

A test procedure must be written before mutation, not after mutation.

Test expectations must be deterministic, reviewable, and reproducible.

Any proposal without test coverage must be rejected.

## Current Scope

The current CP003-B scope is limited to governance and planning documents.

The following checks are allowed in the current phase:

- Git state checks
- Static repository scans
- Documentation consistency checks
- Artifact presence checks
- Hash or manifest verification
- Offline scaffold import checks, if explicitly non-wired
- Baseline non-mutation verification

The following checks are not authorized in the current phase:

- Live trading tests
- Broker connectivity tests
- Runtime wiring tests
- Environment activation tests
- Order placement tests
- Main-loop integration tests
- Production simulation that mutates baseline behavior

## Test Categories

### T1: Repository State Tests

Purpose:

Confirm that the repository is in a controlled state before any review or mutation proposal.

Minimum checks:

- Current branch is `cp003-b-integration-planning`
- Working tree is clean
- Commit ancestry includes `s43-cp003-a-locked`
- Current planning tags are present
- No uncommitted executable mutation exists

Expected result:

- Branch is correct
- Working tree is clean
- Required tags resolve successfully
- No unauthorized files are staged or modified

### T2: Baseline Non-Mutation Tests

Purpose:

Confirm that CP003-B planning has not changed baseline executable files.

Baseline files to protect:

- `s43_instrumented_LATEST.py`
- `11029.py`
- `s43_latest_refactor.py`
- `MY_S43_LATEST.py`

Minimum checks:

- No diff exists between current branch and `s43-cp003-a-locked` for protected baseline files
- No CP003 imports were added to protected baseline files
- No runtime hooks were added to protected baseline files
- No environment activation was added to protected baseline files

Expected result:

- Protected baseline files remain unchanged from the locked CP003-A state
- Static scan returns zero unauthorized wiring matches

### T3: CP003 Scaffold Neutrality Tests

Purpose:

Confirm that CP003 scaffold remains non-executing, deny-by-default, and disconnected from baseline runtime.

Minimum checks:

- `cp003_scaffold` exists as a standalone package
- No baseline file imports `cp003_scaffold`
- `SafetyLawEngine` returns deny-by-default behavior
- `PortfolioBrain` returns hold-only behavior
- `AuditReceiptEngine` creates in-memory objects only
- No network access exists in scaffold code
- No broker call exists in scaffold code
- No file write exists in scaffold code

Expected result:

- Scaffold is importable only as a standalone module
- Scaffold has no side effects on import
- Scaffold does not change baseline runtime authority

### T4: Governance Artifact Tests

Purpose:

Confirm that CP003-B planning artifacts are complete, ordered, and internally consistent.

Required artifacts:

- `governance/CP003_B_INTEGRATION_PLANNING_CHARTER.md`
- `governance/CP003_B_INSERTION_MAP.md`
- `governance/CP003_B_BASELINE_IMPACT_ASSESSMENT.md`
- `governance/CP003_B_SAFETY_GATE_COMPATIBILITY_REVIEW.md`
- `governance/CP003_B_ROLLBACK_PLAN.md`
- `governance/CP003_B_TEST_PLAN.md`

Minimum checks:

- All required files exist
- Each file states runtime integration is unauthorized
- Each file states live trading is unauthorized where applicable
- Each document references the correct branch or governing tag
- Planning artifacts are committed and tagged

Expected result:

- Governance set is complete
- No document grants runtime authority
- No document conflicts with CP003-A lock state

### T5: Future Mutation Preflight Tests

Purpose:

Define the minimum checks that must pass before any future executable mutation proposal.

Required preflight checks:

- Protected baseline file list is declared
- Target insertion point is declared
- Exact function or module to be touched is declared
- Rollback path is declared
- Test execution path is declared
- Safety gate interaction is declared
- Expected behavioral delta is declared
- Failure mode is declared
- Review owner is declared

Expected result:

- Mutation proposal is specific enough to review
- Mutation proposal can be rejected or approved based on evidence
- No hidden integration path exists

### T6: Future Failure-Mode Tests

Purpose:

Define test classes required for any future CP003 integration proposal.

Required future failure-mode tests:

- CP003 import failure
- CP003 exception during evaluation
- CP003 timeout
- CP003 malformed decision output
- Missing audit receipt
- Corrupted audit receipt
- Baseline safety denial
- Emergency stop active
- Broker unavailable
- Environment variable missing
- Configuration invalid
- Partial initialization failure

Expected result:

- Failure modes resolve to deny, hold, disable, or baseline-only behavior
- No failure mode may produce fail-open behavior
- No failure mode may bypass existing safety gates

## Static Scan Requirements

Before any mutation proposal, at least these scans must be run:
```powershell
Select-String -Path ".\s43_instrumented_LATEST.py", ".\11029.py", ".\s43_latest_refactor.py", ".\MY_S43_LATEST.py" -Pattern "cp003_scaffold" -SimpleMatch

Expected result:

- No matches unless a future approved integration explicitly allows a known insertion point.

powershell
git diff --name-status s43-cp003-a-locked..HEAD -- s43_instrumented_LATEST.py 11029.py s43_latest_refactor.py MY_S43_LATEST.py

Expected result:

- No output during planning-only phase.

powershell
git tag --list "s43-cp003-b-*"

Expected result:

- Required CP003-B planning tags are present.

## Future Runtime Test Constraints

If runtime testing is ever proposed in a later authorized phase, it must obey all of the following constraints:

- Must run in offline mode first
- Must not connect to broker by default
- Must not place orders
- Must not require production credentials
- Must not enable live trading authority
- Must not bypass emergency stop checks
- Must not suppress baseline logging
- Must have an explicit rollback path
- Must have a written pass/fail checklist

## Pass Criteria For Current Planning Phase

The current planning phase passes if:

- Working tree is clean
- CP003-B planning documents are committed
- CP003-B planning documents are tagged
- Protected baseline files are unchanged from `s43-cp003-a-locked`
- Static scan shows no unauthorized `cp003_scaffold` wiring
- No document grants runtime integration
- No document grants live trading
- No executable mutation exists beyond previously locked scaffold-only files

## Fail Criteria For Current Planning Phase

The current planning phase fails if:

- Protected baseline files are changed
- Runtime wiring is introduced
- Live trading authority is granted
- Environment activation is added
- Broker connectivity is added
- Scaffold is imported by baseline runtime
- Any planning document contradicts the CP003-A lock
- Any uncommitted mutation exists during review

## Current Ruling

This test plan is documentation-only.

No executable mutation is authorized.

No runtime integration is authorized.

No live trading is authorized.

No broker connectivity is authorized.

No environment activation is authorized.

Any future CP003 integration proposal without deterministic tests must be rejected.
