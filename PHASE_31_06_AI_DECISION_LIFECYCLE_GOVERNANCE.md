<!-- roadmap-metadata {
  "owner": "enterprise-governance",
  "priority": "high",
  "status": "complete",
  "documentation_only": true,
  "depends_on": [
    "PHASE_31_05_AI_DECISION_ENFORCEMENT_AUDIT_EVIDENCE_GOVERNANCE.md"
  ],
  "acceptance_criteria": [
    "AI decision lifecycle governance expectations are documented.",
    "AI decision state transition expectations are documented.",
    "AI decision retirement expectations are documented.",
    "No runtime trading, wallet, execution, or secret-handling logic is modified."
  ],
  "evidence": [
    "AUDIT/AI_DECISION_LIFECYCLE_STANDARD.md",
    "AUDIT/AI_DECISION_STATE_TRANSITION_CONTRACT.md",
    "AUDIT/AI_DECISION_RETIREMENT_CONTRACT.md",
    "ROADMAP_CURRENT.json"
  ],
  "last_verified_at": "2026-06-22T00:00:00Z"
} -->

# Phase 31.06 - AI Decision Lifecycle Governance

Status: Complete.

This phase is documentation-only. It defines governance expectations for the lifecycle of AI-assisted decision records before any future enforcement depends on lifecycle state.

## Purpose

Phase 31.06 establishes lifecycle governance for AI-assisted decisions from initial draft through review, promotion, downgrade, rejection, expiration, and retirement.

The purpose is to ensure that future enforcement gates can reason about decision state without relying on ambiguous, stale, or incomplete records.

## Scope

This phase covers:

- AI decision lifecycle states.
- Allowed state transition expectations.
- Retirement and expiration expectations.
- Stale decision handling.
- Governance expectations for future CI and audit enforcement.

This phase does not implement runtime enforcement, automated lifecycle tracking, trading behavior, wallet interaction, model execution, or secret-handling logic.

## Lifecycle States

AI-assisted decision records should use clear lifecycle states such as:

- draft
- advisory-only
- review-ready
- promotion-ready
- promoted
- blocked
- rejected
- invalid
- expired
- retired

A decision should not be treated as promotion-ready unless required evidence, review expectations, and readiness expectations are satisfied.

## Transition Expectations

Lifecycle transitions should be explicit, reviewable, and supported by evidence.

Direct promotion from draft or advisory-only to promoted should not occur without intermediate evidence and review readiness. Blocked, rejected, invalid, expired, or retired records should not be promoted without a new reviewable decision record or approved governance exception.

## Retirement Expectations

AI decision records should be retired when they are no longer valid, superseded by a newer decision, tied to expired evidence, or no longer suitable for enforcement-sensitive workflows.

Retired records should remain reviewable for audit purposes but should not be used as active promotion or enforcement evidence.

## Future Enforcement Direction

Potential future enforcement actions may include:

- Failing CI when lifecycle state transitions are unsupported.
- Blocking release approval when promotion-ready records are stale or expired.
- Downgrading decisions when required lifecycle evidence is missing.
- Requiring retirement references for superseded AI decision records.
- Producing structured lifecycle audit summaries.

## Acceptance Criteria

This phase is complete when:

- AI decision lifecycle governance is documented.
- AI decision state transition expectations are documented.
- AI decision retirement expectations are documented.
- Roadmap metadata records this phase as documentation-only.
- The operational roadmap generator and validator pass.
