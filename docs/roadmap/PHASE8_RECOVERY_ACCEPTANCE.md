# Phase 8 Recovery Acceptance Criteria

## Scope

This document defines documentation-only acceptance criteria for any future consideration of runtime recovery work during Phase 8. It does not authorize implementation, activation, or testing against live trading behavior. The repository remains in `SAFE-NO-TRADE`.

## Explicit Non-Goals

- No modification of `s43.py` runtime recovery behavior in this step.
- No activation of automatic runtime recovery.
- No live trading enablement.
- No changes to Arzplus authorization logic.
- No changes to token acquisition, token refresh, or token storage schemes.
- No changes to exchange endpoints.
- No weakening of existing safety guards, veto paths, or hard-stop behavior.
- No dependence on operator secrets or live exchange conditions for acceptance.

## Preconditions for Any Future Recovery Work

Any future recovery-related code change must be blocked until all of the following are true:

1. The intended recovery scenario is documented in plain language, including trigger, expected behavior, and safe failure mode.
2. The exact runtime touchpoints are identified in documentation before any code edit is proposed.
3. A rollback path is documented and practical.
4. The change can be validated without enabling live trading.
5. The change does not require modifying Arzplus auth/token/endpoint behavior as part of the same step.
6. Existing hardening tests continue to pass cleanly.
7. Any new tests introduced are deterministic, offline-safe, and CI-safe wherever possible.

## Required Test Evidence Before Any Activation Is Considered

Before any future activation discussion, the following evidence should exist:

- A documentation-backed inventory of recovery touchpoints.
- Focused tests for the intended recovery decision points.
- Negative-path tests showing safe no-op or hard-stop behavior under failure conditions.
- Regression evidence showing no impact to existing safeguards.
- Clean execution of `python3 run_hardening_tests.py`.

## Safety Guardrails

Any future recovery proposal must preserve all of the following:

- `SAFE-NO-TRADE` remains the default state until an explicit later decision says otherwise.
- No broadening from allowlisted test execution to uncontrolled discovery.
- No coupling of recovery work with unrelated refactors.
- No hidden dependency on operator-specific environment setup for core validation.
- No suppression of observability or safety logging tied to failure handling.
- No silent fallback that masks authorization, balance, or data integrity failures.

## Abort Conditions

Any future recovery-related proposal should be rejected or deferred if any of the following is true:

- It requires auth/token/endpoint changes in the same step.
- It cannot be validated offline or without live trading exposure.
- It reduces the strength or clarity of existing safety guards.
- It introduces ambiguous behavior under exchange failure, HTTP 403, missing data, or wallet refresh errors.
- It lacks a clear rollback path.
- It expands scope beyond documentation, isolated tests, or narrowly bounded code review preparation.

## Approval Checklist

Before any future implementation-oriented recovery step is approved, confirm:

- [ ] Scope is narrowly defined.
- [ ] Non-goals are explicit.
- [ ] Runtime touchpoints are documented.
- [ ] Preconditions are satisfied.
- [ ] Required tests are identified.
- [ ] Rollback path is documented.
- [ ] No live trading enablement is involved.
- [ ] No auth/token/endpoint change is bundled in.
- [ ] Hardening runner remains green.
- [ ] Repository safety posture remains `SAFE-NO-TRADE`.

## Suggested Next Documentation Step

After this document, the next safest step is to create a documentation-only inventory of runtime recovery touchpoints, with references to the relevant modules, control flow anchors, and guardrails, without changing runtime behavior.
