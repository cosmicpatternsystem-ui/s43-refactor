# AI Decision State Transition Contract

## Purpose

This contract defines expectations for state transitions in AI-assisted decision records.

The contract is documentation-only and does not implement transition validation, runtime checks, or automated approval behavior.

## Transition Objectives

State transitions should be:

- Explicit.
- Evidence-backed.
- Reviewable.
- Attributable to a policy, contract, or operator disposition.
- Consistent with the prior decision state.
- Free of secrets and unredacted credentials.

## Transition Expectations

A transition should identify the prior state, next state, reason for transition, supporting evidence, timestamp or lifecycle event, and reviewer or operator disposition when applicable.

Direct transition to promoted status should require evidence that the record was review-ready or promotion-ready before promotion.

## Transition Failure Conditions

A transition should not support promotion when:

- Required evidence is missing.
- Prior state is ambiguous.
- Review disposition is absent.
- Evidence is unreachable.
- The decision has expired.
- The decision has been rejected, invalidated, or retired.
- Secrets or unredacted credentials are present.

## Future Enforcement Direction

Future phases may map transition expectations to CI failures, release approval gates, lifecycle audit reports, and governance exception handling.
