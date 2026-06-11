# Phase 8 Roadmap

## Status

The repository is currently stable after Phase 7C cleanup and hardening.

Current baseline:

- Runtime remains SAFE-NO-TRADE.
- Arzplus HTTP 403 is treated as an exchange-side temporary issue.
- No live trading path should be enabled.
- Phase 6 deterministic hardening runner exists.
- Phase 7C NO_DATA:USDT_PX guard is validated.
- PARISA_VETO and consumer veto behavior are validated by dedicated tests.
- Documentation and audit artifacts have been cleaned and archived.

## Phase 8 Goal

Phase 8 focuses on safe preparation for future runtime recovery and CI/test hardening.

Phase 8 must not:

- change Arzplus authorization behavior
- change token scheme
- change base_url
- change endpoints
- enable buy/sell/order placement
- enable live trading
- weaken SAFE-NO-TRADE behavior

## Main Tracks

### Track A: Phase 7 Hardening Index

Create a consolidated index of the completed Phase 7 hardening work, including:

- NO_DATA:USDT_PX guard
- PARISA_VETO behavior
- consumer hard-stop behavior
- related tests
- related tags/commits
- expected safety contracts

### Track B: Excluded Test Audit

Review tests currently excluded from the Phase 6 allowlisted runner:

- test_arzplus_tokens_strict.py
- test_reporting_summary_regression.py

For each test, decide whether it is:

1. deterministic
2. offline-safe
3. CI-safe
4. free of network/live-trading dependency
5. suitable for promotion into run_hardening_tests.py

No test should be promoted until this audit is complete.

### Track C: Operator Runbook

Create a safe runtime runbook covering:

- wallet slot environment variables
- safe check commands
- expected HTTP 403 behavior
- cooldown behavior
- post-recovery validation checklist
- explicit no-live-trading warning

### Track D: Post-Recovery Validation Plan

Prepare, but do not execute prematurely, a checklist for after Arzplus recovers from HTTP 403:

1. compile check
2. wallet 1 safe check
3. wallet 2 safe check
4. wallet 3 safe check
5. all-wallet safe check
6. confirm no runtime crash
7. confirm no unsafe order path
8. confirm no unexpected auth mutation

## Recommended First Implementation Step

Do documentation-only Phase 8 bootstrap:

1. add this roadmap
2. add Phase 7 hardening index
3. add operator runbook
4. audit excluded tests without modifying production code

## Production Code Policy

Phase 8 starts as documentation and test-orchestration hardening only.

No production code change is allowed unless a specific test-backed safety gap is identified.

## Current Decision

The safest next move is:

- Do not modify s43.py yet.
- Do not change Arzplus auth.
- Do not enable trading.
- Create Phase 8 roadmap and supporting docs.
- Then audit excluded tests for possible allowlist promotion.

