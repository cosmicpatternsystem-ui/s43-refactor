# CP003-B Rollback Plan

## Status

- Phase: CP003-B
- Document type: Rollback Plan
- Branch: cp003-b-integration-planning
- Base lock tag: s43-cp003-a-locked
- Charter tag: s43-cp003-b-charter-v1
- Insertion Map tag: s43-cp003-b-insertion-map-v1
- Impact Assessment tag: s43-cp003-b-impact-assessment-v1
- Safety Gate Review tag: s43-cp003-b-safety-gate-review-v1
- Runtime integration: UNAUTHORIZED
- Live trading: UNAUTHORIZED
- Baseline executable mutation: UNAUTHORIZED

## Purpose

This document defines the rollback strategy that must exist before any future executable CP003 integration is proposed.

This document is planning-only.

It does not authorize mutation, runtime integration, live trading, or any destructive repository action.

## Rollback Principle

Any future CP003 integration must be reversible, explicit, and fast.

Rollback must restore the last known safe baseline behavior without ambiguity.

Rollback must prefer deterministic recovery over partial recovery.

Rollback must not depend on live judgment during an incident.

## Safe Reference Points

The following repository states are recognized as rollback reference points:

- Baseline locked state:
  - Commit: 1f65034a92afa4bd10d7cf20e4fd07266387372e
  - Tag: s43-cp003-a-locked

- CP003-B planning start:
  - Commit ancestry includes baseline lock
  - Tag: s43-cp003-b-start

- CP003-B charter:
  - Commit: 6da4b3e05e55eaaaa6d9427abf372699045ed8d6
  - Tag: s43-cp003-b-charter-v1

- CP003-B insertion map:
  - Commit: 8369483201c87dd66e0e9ae42f6fff8008bbc94d
  - Tag: s43-cp003-b-insertion-map-v1

- CP003-B impact assessment:
  - Commit: 2428a6c452f20a4a94e73bb081d61b5b17805365
  - Tag: s43-cp003-b-impact-assessment-v1

- CP003-B safety gate review:
  - Commit: d57f92b9f2ad7e4f76f043827c826a80f308ca47
  - Tag: s43-cp003-b-safety-gate-review-v1

These are governance reference points, not instructions to rewrite history.

## Rollback Trigger Classes

If future integration is ever authorized, rollback planning must account for at least the following trigger classes:

### Class R1: Safety Degradation

Examples:

- Existing baseline safety gates stop firing as expected
- Emergency stop behavior changes
- Safety output becomes inconsistent
- Fail-open behavior is observed

Required default response:

- Disable CP003 integration path immediately
- Preserve audit evidence
- Return to baseline-only authority

### Class R2: Runtime Instability

Examples:

- Import failures
- Unhandled exceptions
- Timeouts
- Main loop latency increase
- Resource exhaustion

Required default response:

- Remove CP003 from execution path
- Restore deterministic baseline flow
- Record failure mode

### Class R3: Audit Integrity Failure

Examples:

- Missing receipts
- Corrupted receipts
- Non-deterministic receipt output
- Logging interference
- Masked baseline exceptions

Required default response:

- Disable dependent CP003 audit hook
- Preserve baseline logs
- Record integrity incident

### Class R4: Behavioral Drift

Examples:

- Order timing changes
- Order sizing changes
- Position state divergence
- Decision sequence drift
- Unexpected interaction with broker connectivity

Required default response:

- Revert to pre-integration behavior
- Compare against baseline expectations
- Block further rollout

## Rollback Scope Rules

Any future rollback plan for an executable mutation must define all of the following scopes:

- File-level rollback scope
- Function-level rollback scope
- Configuration rollback scope
- Import-path rollback scope
- Logging/audit rollback scope
- Test harness rollback scope
- Deployment/runtime flag rollback scope, if any

Rollback scope must be exact, not approximate.

## Mandatory Rollback Properties

Any future executable integration must satisfy these rollback properties:

- CP003 path can be disabled without deleting baseline logic
- Baseline path remains intact and callable
- CP003 exceptions do not corrupt baseline state
- Rollback does not require broker-side intervention
- Rollback does not require data migration in the hot path
- Rollback can be performed with written steps
- Rollback success can be verified with deterministic checks

## Required Rollback Artifacts Before Mutation

Before any executable mutation is proposed, the following rollback artifacts must exist:

- Named rollback owner
- Trigger-to-action matrix
- Step-by-step rollback procedure
- Verification checklist
- Expected post-rollback baseline behavior
- List of files touched by the mutation
- List of functions touched by the mutation
- Log evidence collection plan
- Safe disable switch definition
- Re-entry criteria after rollback

## Disallowed Rollback Assumptions

The following assumptions are not acceptable in a future mutation proposal:

- "Rollback will be easy"
- "Restarting should fix it"
- "We can patch live if needed"
- "The scaffold should fail safely by default" without proof
- "The baseline probably still works" without verification
- "The broker session will recover automatically"
- "Receipts are optional during incident handling"

## Verification Requirements After Rollback

Any future rollback execution must be verified with at least:

- Baseline imports succeed
- Baseline startup succeeds
- Baseline safety gates remain active
- No CP003 runtime dependency remains on the execution path
- No change in live trading authority is introduced
- Audit/log output remains available
- Expected baseline control flow is restored

## Current Ruling

This rollback plan is documentation-only.

No rollback action is being executed.

No history rewrite is authorized.

No executable mutation is authorized.

No runtime integration is authorized.

Any future integration proposal that lacks an explicit rollback procedure must be rejected.
