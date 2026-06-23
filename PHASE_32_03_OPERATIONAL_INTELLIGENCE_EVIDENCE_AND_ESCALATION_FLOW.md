# Phase 32.03 — Operational Intelligence Evidence and Escalation Flow

## Objective
Define the minimum evidence model and escalation flow for the Operational Intelligence Runtime so that every significant runtime decision is observable, classifiable, reviewable, and reproducible.

## Scope
This phase defines:
- evidence artifact categories
- severity and confidence bands
- escalation triggers
- blocking and override pathways
- audit and replay requirements

This phase does not yet define:
- UI presentation details
- external notification integrations
- long-term evidence retention policy
- cross-environment federation

## Required Evidence Artifacts
The runtime must be able to emit, persist, or reference the following evidence classes for every significant operational decision:
- input snapshot
- normalized context snapshot
- active policy/gate snapshot
- derived signals
- decision result
- enforcement action
- operator-visible rationale
- replay handle or correlation id

## Signal Classification Contract
Each derived signal should include, at minimum:
- signal name
- signal category
- severity level
- confidence level
- source provenance
- timestamp
- correlation id

### Severity Levels
- `info`
- `warning`
- `elevated`
- `critical`

### Confidence Bands
- `low`
- `medium`
- `high`

## Escalation Triggers
Escalation should be activated when one or more of the following conditions are met:
- a `critical` signal is emitted
- multiple `elevated` signals co-occur within the same decision window
- policy ambiguity prevents deterministic enforcement
- evidence integrity is incomplete or unverifiable
- a blocking gate cannot establish a safe pass condition
- repeated override behavior exceeds defined tolerance

## Escalation Paths
The runtime should support the following paths:
- `pass`: normal execution with evidence recorded
- `warn`: execution continues with operator-visible warning
- `hold`: execution pauses pending review or retry
- `block`: execution is prevented by policy or safety gate
- `override`: execution proceeds only with explicit privileged acknowledgement and mandatory evidence capture

## Override Contract
Every override event must record:
- actor identity
- reason code
- freeform rationale
- affected decision scope
- timestamp
- related evidence references
- resulting action state

## Audit and Replay Requirements
For each escalated or blocked decision, the system should preserve enough information to:
- reconstruct the decision context
- identify the triggering signals
- identify the governing policy state
- verify the action taken
- replay the decision path for review

## Verification Gates
This phase is considered complete when:
- the evidence artifact contract is documented
- escalation path semantics are documented
- override requirements are documented
- audit/replay minimums are documented
- roadmap generation and validation succeed

## Exit Criteria
- evidence requirements are implementation-ready
- escalation semantics are unambiguous
- downstream phases can bind enforcement and observability to this contract
