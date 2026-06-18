# Abstract Policy Engine Plan

Date: 2026-06-18

## Current Baseline

- Baseline tag: `g11-active-guarded-mode-20260618`
- Runtime mode: `G11_ACTIVE_GUARDED_MODE`
- G11 smoke tests: PASSED
- Working tree: clean

## Objective

Introduce an Abstract Policy Engine as a non-invasive orchestration layer for safety gates, risk policies, and execution constraints.

## Phase 1 Scope

- Design only
- No runtime behavior change
- No replacement of existing G11 guards
- No live trading path modification

## Policy Domains

1. Capital protection
2. Wallet-cycle protection
3. Per-symbol exposure limits
4. Runtime halt policy
5. Audit event normalization
6. Operator override policy

## Proposed Interfaces

- `PolicyContext`
- `PolicyDecision`
- `PolicyRule`
- `PolicyEngine`

## Decision Model

Each policy evaluation should return:

- `ALLOW`
- `WARN`
- `BLOCK`
- `HALT`

## Integration Rule

Existing G11 guards remain the source of truth until the policy engine passes isolated smoke tests and shadow-mode validation.

## Next Gate

Create a shadow-mode policy engine prototype that can evaluate synthetic contexts without touching live execution paths.
