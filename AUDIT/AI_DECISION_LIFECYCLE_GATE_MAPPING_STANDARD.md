# AI Decision Lifecycle Gate Mapping Standard

## Purpose

This standard defines governance expectations for mapping AI-assisted decision lifecycle states and evidence conditions to future enforcement-sensitive gate outcomes.

The standard is documentation-only and does not add runtime enforcement, automated gate evaluation, CI release blocking, trading behavior, wallet interaction, model execution, or secret-handling logic.

## Mapping Objectives

Lifecycle gate mapping should support:

- Predictable gate outcomes.
- Conservative handling of incomplete or failed evidence.
- Reviewable mapping between lifecycle state and gate result.
- Explicit handling of exceptions.
- Consistent treatment of stale, expired, invalid, rejected, blocked, and retired records.
- Future CI, release, and audit gate evaluation.

## Lifecycle State Mapping

Expected lifecycle state treatment:

- `draft`: not gate-ready.
- `advisory-only`: advisory use only; not enforcement-approval-ready.
- `review-ready`: eligible for human or governance review.
- `promotion-ready`: eligible for future gate evaluation when evidence is complete.
- `promoted`: eligible only while supporting evidence remains valid and reviewable.
- `blocked`: not approval-ready.
- `rejected`: not approval-ready unless replaced by a new reviewable record.
- `invalid`: not approval-ready.
- `expired`: not approval-ready unless renewed through documented governance.
- `retired`: reviewable for history but not active promotion evidence.

## Evidence Mapping

Evidence condition treatment should be conservative:

- Complete evidence may support gate evaluation.
- Incomplete evidence should block or defer gate approval.
- Failed evidence should prevent enforcement-sensitive approval.
- Stale evidence should be treated as incomplete or failed.
- Unreachable evidence should be treated as incomplete or failed.
- Secret-bearing evidence should fail the gate until remediated.
- Exception-backed evidence should remain limited, explicit, and reviewable.

## Non-Goals

This standard does not define storage backends, approval systems, release automation, runtime logging, model serving behavior, trading execution controls, wallet authorization, automated gate implementation, or credential management implementation.
