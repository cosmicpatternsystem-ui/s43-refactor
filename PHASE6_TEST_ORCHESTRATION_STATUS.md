# Phase 6 Test Orchestration Status

## Scope

Phase 6 focuses on test orchestration and CI hardening.

The goal is to provide a deterministic local and CI entrypoint for the Phase 5 observability hardening tests, without modifying s43.py and without relying on broad test discovery.

## Runner

The allowlisted runner is:

run_hardening_tests.py

It executes only the explicitly approved hardening tests:

test_status_observability_summary
test_status_observability_wallet_error
test_status_observability_obs_format

## Rationale

The runner intentionally avoids generic discovery such as:

python3 -m unittest discover

The repository contains many unrelated, historical, backup, audit, log, patch, snapshot, cache, and experimental files.

Broad discovery could accidentally include unstable, irrelevant, network-dependent, or unsafe tests.

Using an explicit allowlist keeps execution deterministic and suitable for local hardening and future CI integration.

## Included Tests

The Phase 6 runner currently includes:

test_status_observability_summary.py
test_status_observability_wallet_error.py
test_status_observability_obs_format.py

These tests cover the Phase 5 observability hardening contract for:

- wallet_reporting_summary
- wallet_balance_error
- general OBS output format

## Excluded Tests

The following tracked tests are intentionally not included in the Phase 6 runner yet:

test_arzplus_tokens_strict.py
test_reporting_summary_regression.py

They should remain excluded until their dependencies, offline behavior, runtime safety, and CI suitability are reviewed separately.

## Production Code Policy

No Phase 6 runner change modifies s43.py.

The runner imports and executes the existing allowlisted hardening tests only.

## Commands

Compile check:

python3 -m py_compile run_hardening_tests.py

Run hardening suite:

python3 run_hardening_tests.py

Expected result:

Ran 3 tests
OK

A skipped test may be acceptable only if the individual test has an intentional runtime skip condition.

## References

Phase 6 baseline:

phase6-test-orchestration-baseline-20260531
backup/phase6-test-orchestration-baseline

Runner commit:

b1a637c Add allowlisted hardening test runner

Runner tag:

phase6-test-orchestration-runner-20260531

Runner backup branch:

backup/phase6-test-orchestration-runner

## Current Status

The Phase 6 allowlisted runner has been created, compiled, executed, committed, tagged, and backed up.

The next safe step after this document is to decide whether to add a minimal CI wrapper or keep Phase 6 local-only for now.

## CI Wrapper

A minimal GitHub Actions workflow has been added:

.github/workflows/hardening-tests.yml

The workflow intentionally runs only the deterministic Phase 6 hardening commands:

python3 -m py_compile s43.py run_hardening_tests.py
python3 run_hardening_tests.py

It does not run broad unittest discovery.

It does not install additional dependencies.

It does not modify production code.

## CI Wrapper Reference

CI wrapper commit:

6787c21 Add minimal hardening tests GitHub Actions workflow

CI wrapper tag:

phase6-test-orchestration-ci-wrapper-20260531

CI wrapper backup branch:

backup/phase6-test-orchestration-ci-wrapper

## Final Phase 6 Status

Phase 6 now includes both:

- local deterministic hardening test orchestration
- minimal GitHub Actions CI wrapper

The Phase 6 contract remains allowlist-only and does not modify s43.py.
