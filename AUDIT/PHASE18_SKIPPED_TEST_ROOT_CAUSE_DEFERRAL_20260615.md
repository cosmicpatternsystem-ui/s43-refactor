# Phase 18 Skipped Test Root-Cause Deferral - 2026-06-15

## Decision

The project currently recognizes an external test result of:
```text
57 passed, 2 skipped

The two skipped tests are not being modified in this workspace at this time.

## Rationale

- The active workspace does not contain the real test suite responsible for the skipped tests.
- No tracked test files, skip markers, skipif markers, or xfail markers were found in the available workspace scope.
- A root-cause fix requires access to the actual skipped tests, their fixtures, and their execution environment.
- Any attempted fix without those inputs would be speculative and would violate Phase 18 release-candidate hardening standards.

## Commercial Release Candidate Impact

- The skipped tests are recorded as a stability-readiness risk.
- The skipped tests are not currently approved as resolved.
- Conversion from 57 passed / 2 skipped to 59 passed remains a Phase 18 hardening objective.
- This deferral does not authorize feature work, behavioral refactor, or speculative product changes.

## Required Inputs For Root-Cause Resolution

At least one of the following inputs is required before remediation can begin:

1. Full output of `pytest -ra` from the environment that reports the two skipped tests.
2. The actual test files containing the skipped tests.
3. The original test workspace including `tests/`, `conftest.py`, `pytest.ini`, `pyproject.toml`, or equivalent configuration.

## Approved Future Resolution Path

When the required inputs are available, the approved path is:

1. Identify the exact skipped tests by node id.
2. Identify the skip mechanism and condition.
3. Determine whether the skip is caused by missing fixture, missing dependency, environment gating, or product behavior.
4. Apply the smallest root-cause fix.
5. Re-run the relevant test subset.
6. Re-run the full suite and confirm:

text
59 passed, 0 skipped

## Current Classification

text
CLASSIFICATION=KNOWN_STABILITY_GAP_DEFERRED_PENDING_TEST_SOURCE
ACTION_NOW=NO_SPECULATIVE_FIX
ACTION_LATER=ROOT_CAUSE_REMEDIATION_REQUIRED_WHEN_TESTS_AVAILABLE
PHASE18_POLICY=FEATURE_FREEZE_AND_RELEASE_CANDIDATE_HARDENING
