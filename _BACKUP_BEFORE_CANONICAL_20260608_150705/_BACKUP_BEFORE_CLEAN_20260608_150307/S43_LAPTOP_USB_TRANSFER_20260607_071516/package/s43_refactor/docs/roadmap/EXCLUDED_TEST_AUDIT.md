# Excluded Test Audit

## Purpose

This document reviews tests currently excluded from the Phase 6 allowlisted hardening runner.

The goal is to decide whether any excluded test is suitable for controlled promotion into `run_hardening_tests.py`.

This audit must not modify production runtime behavior.

## Current Scope

The currently known excluded tests are:

- test_arzplus_tokens_strict.py
- test_reporting_summary_regression.py

These tests are not automatically promoted just because they exist.

Each test must be reviewed for determinism, offline safety, CI suitability, and runtime safety.

## Audit Criteria

A test is eligible for promotion only if it is confirmed to be:

1. deterministic
2. offline-safe
3. CI-safe
4. free from live-trading dependency
5. free from exchange/network dependency
6. compatible with explicit allowlist execution
7. not dependent on unstable historical artifacts
8. not dependent on local secrets or operator-only environment state

## Test 1: test_arzplus_tokens_strict.py

### Initial Risk Questions

- Does the test depend on real environment tokens?
- Does the test require network access?
- Does the test make assumptions about exchange auth behavior that are unstable during HTTP 403 conditions?
- Does the test remain safe when no real wallet access is available?
- Does the test exercise only local token-resolution logic, or does it drift into runtime/exchange behavior?

### Promotion Decision

Current decision: NOT YET PROMOTED

Reason:

- requires explicit audit of token/environment dependence
- must be proven offline-safe before allowlist inclusion
- must not create pressure to alter auth behavior during exchange instability

## Test 2: test_reporting_summary_regression.py

### Initial Risk Questions

- Is the test fully deterministic?
- Does it depend on historical output formatting that may be noisy or brittle?
- Does it rely on logs, snapshots, or artifacts outside a stable test contract?
- Is it independent from network and live runtime conditions?
- Is it suitable for CI without special setup?

### Promotion Decision

Current decision: NOT YET PROMOTED

Reason:

- requires explicit audit of regression expectations
- must be shown not to depend on brittle formatting or unstable fixtures
- must be proven suitable for deterministic CI execution

## Required Audit Method

Before promotion, each excluded test should be reviewed using this sequence:

1. read the test file
2. identify imports and dependencies
3. identify any network/runtime coupling
4. identify any environment-variable coupling
5. identify any file/log/snapshot coupling
6. run individually if safe
7. decide: promote / keep excluded / refactor later

## Promotion Policy

A test may be promoted only if:

- it passes reliably in isolation
- it does not require live exchange access
- it does not require production secrets
- it does not broaden execution into unsafe discovery behavior
- it strengthens the hardening contract meaningfully

If any of those conditions fail, the test remains excluded.

## Current Decision

At the current Phase 8 state:

- no excluded test is promoted yet
- audit comes before promotion
- no production code change is authorized as part of this audit
- any future promotion must be explicit and documented

## Next Safe Step

The next safe implementation step after this document is:

- inspect the two excluded test files directly
- classify each one against the audit criteria
- record a promote / keep-excluded recommendation

## Audit Result

### test_arzplus_tokens_strict.py

Observed characteristics:

- imports `s43` directly
- reads real environment variables via `os.getenv`
- enforces machine/operator-specific token expectations
- requires slot 1 = SET, slot 2 = EMPTY, slot 3 = SET
- rejects generic fallback token variables
- validates live local resolver behavior against current shell environment

Assessment:

- deterministic: NO
- offline-safe: YES
- CI-safe: NO
- network/exchange dependent: NO
- environment dependent: YES
- suitable for allowlisted hardening runner: NO

Decision:

- KEEP EXCLUDED

Reason:

This file behaves as an operator/local-environment strict validation script, not a repository-wide deterministic CI-safe test.

Future option:

- refactor later into either:
  - an operator utility script, or
  - a true unit test using controlled environment mocking

### test_reporting_summary_regression.py

Observed characteristics:

- uses local dummy wallet/bot test doubles
- performs no real network activity
- requires no secrets or operator environment state
- checks deterministic summary-count behavior
- checks disabled-wallet accounting contract
- checks summary-string regression contract
- includes local fallback helpers if `s43` helper functions are absent

Assessment:

- deterministic: YES
- offline-safe: YES
- CI-safe: YES
- network/exchange dependent: NO
- environment dependent: NO
- suitable for allowlisted hardening runner: YES

Decision:

- ELIGIBLE FOR PROMOTION

Reason:

This test is deterministic, local-only, and meaningfully protects reporting summary behavior without introducing exchange/runtime risk.

## Recommended Next Action

If promotion is implemented, promote only:

- test_reporting_summary_regression.py

Do not promote:

- test_arzplus_tokens_strict.py

No production runtime change is required for this decision.

## Promotion Implementation Note

`test_reporting_summary_regression.py` was not discoverable through the
existing `unittest.TestLoader().loadTestsFromName(...)` path
(`countTestCases() == 0`).

To preserve the explicit allowlist safety model without modifying production
code or rewriting the test module, promotion was implemented in
`run_hardening_tests.py` via a separate script-style allowlist path.

This preserves:
- explicit allowlisting
- no broad test discovery
- no `s43.py` runtime change
- continued exclusion of `test_arzplus_tokens_strict.py`
