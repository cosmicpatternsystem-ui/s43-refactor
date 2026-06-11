# Phase 8 Recovery Runtime Touchpoints Inventory

## Purpose

This document provides a documentation-only inventory of runtime touchpoints that would need explicit review before any future recovery-related implementation is considered during Phase 8.

It does not authorize code changes, runtime activation, live trading behavior, endpoint changes, or Arzplus authorization changes. The repository remains in `SAFE-NO-TRADE`.

## Scope

This inventory is intended to identify where recovery behavior could interact with runtime control flow, safety decisions, external dependency handling, and observability.

It is not an implementation plan.

## Explicit Non-Goals

- No modification of `s43.py` in this step.
- No activation of automatic runtime recovery.
- No live trading enablement.
- No changes to Arzplus authorization logic.
- No changes to token acquisition, token refresh, or token persistence behavior.
- No changes to exchange endpoints.
- No changes to order placement, wallet refresh, or trade execution behavior.
- No weakening of existing hard-stop, veto, or fail-closed behavior.
- No introduction of recovery behavior that depends on operator-specific live environment state.

## Touchpoint Categories Requiring Prior Review

Any future recovery proposal must first document whether it interacts with one or more of the following categories.

### 1. Process Lifecycle and Main Loop Control

Potential touchpoints include:
- Main runtime loop entry and exit conditions
- Retry boundaries
- Restart or re-entry logic
- State transitions after exceptions
- Timing, cooldown, or backoff control flow

Guardrails:
- No automatic restart behavior should be introduced without explicit bounded conditions.
- Failure handling must remain visible and auditable.
- Infinite retry risk must be explicitly ruled out.

### 2. Safety Guards and Veto Paths

Potential touchpoints include:
- Existing kill-switch or hard-stop paths
- Safety validation gates
- No-trade enforcement logic
- Conditions that intentionally prevent continuation after unsafe states

Guardrails:
- Existing veto behavior must not be weakened.
- Recovery must not bypass safety checks.
- Fail-closed behavior must remain the default.

### 3. Authorization and Session State Boundaries

Potential touchpoints include:
- Authentication state assumptions
- Session continuity expectations
- Authorization failure handling
- HTTP 401/403 response handling
- Token-related decision branches

Guardrails:
- No recovery work may bundle auth or token behavior changes in the same step.
- Authorization failures must not be masked by silent fallback.
- Any dependency on session recovery must be documented separately before implementation is considered.

### 4. Exchange/Network Failure Handling

Potential touchpoints include:
- HTTP request failure handling
- Timeout behavior
- Retries against external services
- Handling of malformed or partial responses
- Distinguishing transient failure from unsafe state

Guardrails:
- Recovery must not convert unclear exchange state into assumed-safe continuation.
- Retry behavior must be bounded and observable.
- Partial or stale data must not be treated as valid recovery state without explicit evidence.

### 5. Wallet, Balance, and Asset State Refresh

Potential touchpoints include:
- Wallet refresh control flow
- Balance read failures
- Missing asset data
- Partial refresh behavior
- Consistency checks between cached and fresh state

Guardrails:
- Recovery must not hide balance or wallet refresh failures.
- Missing financial state must remain a stop condition unless separately justified and tested.
- Data integrity takes priority over liveness.

### 6. Order/Execution Adjacency

Potential touchpoints include:
- Any code path near order creation or order follow-up
- State assumptions immediately before or after trade-related decisions
- Cleanup logic after interrupted execution flows

Guardrails:
- No recovery proposal may move the system closer to trade execution without explicit later approval.
- Recovery work must remain isolated from order placement semantics.
- No silent continuation from uncertain execution state.

### 7. Persistence, Cache, or Local Runtime State

Potential touchpoints include:
- Temporary runtime state
- Cached decision inputs
- Local files or serialized state
- Re-entry assumptions after partial progress

Guardrails:
- Recovery must not rely on undocumented local state.
- Cached state must not override fresh safety-critical checks.
- Any persistence-related behavior must be deterministic and reviewable.

### 8. Logging, Reporting, and Observability

Potential touchpoints include:
- Error logging paths
- Warning and status reporting
- Recovery attempt visibility
- Summary/reporting outputs tied to failure conditions

Guardrails:
- Recovery logic must not reduce observability.
- Operator-visible evidence of failure and recovery decisions must be preserved.
- Reporting changes must not obscure hard-stop outcomes.

## Review Questions Required Before Any Code Change

Before any future recovery-related code proposal, answer all of the following in documentation:

1. What exact failure scenario is being addressed?
2. Where does that scenario enter runtime control flow?
3. Which safety guards already apply there?
4. What is the proposed no-op or fail-closed behavior if recovery is not possible?
5. How is infinite retry or oscillation prevented?
6. How is authorization ambiguity prevented from becoming runtime continuation?
7. How is stale, partial, or missing wallet/data state handled safely?
8. What evidence shows no increased live-trading risk?
9. What rollback path exists if the change behaves unexpectedly?
10. How will the change be validated offline?

## Minimum Evidence Required Before Any Implementation Step

Before implementation-oriented recovery work is considered, the following should exist:

- A documented mapping from recovery scenario to runtime touchpoints
- A statement of why existing behavior is insufficient
- Focused negative-path tests for the exact decision points involved
- Regression evidence showing no weakening of hardening behavior
- Clean execution of `python3 run_hardening_tests.py`
- A documented rollback strategy
- Explicit confirmation that no auth/token/endpoint change is bundled into the same step

## Safe Sequencing Recommendation

The safest sequence for any future recovery work is:

1. Documentation of the target scenario
2. Documentation of exact runtime touchpoints
3. Documentation of guardrails and rollback path
4. Focused offline-safe tests
5. Separate review of whether code changes should happen at all
6. Only then, if approved later, narrowly bounded implementation review

## Current Phase 8 Recommendation

At the current stage, this repository should remain in documentation and hardening mode only.

Recommended current posture:
- Keep `SAFE-NO-TRADE`
- Avoid `s43.py` runtime edits
- Avoid auth/token/endpoint changes
- Avoid recovery activation
- Prefer auditability, bounded scope, and offline-safe validation

## Conclusion

This inventory exists to reduce the chance of unsafe or overly broad recovery changes by forcing documentation of runtime-sensitive touchpoints before implementation is considered.

It is a planning and safety artifact only, not an implementation approval.
