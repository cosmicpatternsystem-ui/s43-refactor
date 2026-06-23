# Phase 32.04 — Operational Intelligence Verification and Replay Contract

## Objective
Define the minimum verification and replay contract for the Operational Intelligence Runtime so that decisions can be deterministically re-evaluated, audited, and compared against their original enforcement outcome.

## Scope
This phase defines:
- replay unit boundaries
- verification artifact requirements
- deterministic re-evaluation expectations
- comparison semantics between original and replayed outcomes
- audit-grade replay result requirements

This phase does not yet define:
- production-scale replay orchestration
- distributed replay scheduling
- historical storage tiering strategy
- cross-system replay federation

## Replay Unit Contract
A replay unit is the minimum self-contained package required to re-evaluate a runtime decision. Each replay unit should include, at minimum:
- input snapshot
- normalized context snapshot
- governing policy/gate snapshot
- derived signals snapshot
- original decision result
- enforcement action record
- evidence references
- correlation id
- decision timestamp

## Verification Artifact Requirements
Each verification event should produce or reference artifacts that allow an operator or audit process to determine:
- what was originally decided
- what inputs and policies governed the decision
- what replay execution was performed
- whether the replay matched the original outcome
- what mismatches, if any, were observed

## Deterministic Re-evaluation Contract
Replay should, where contractually possible, re-evaluate the same decision using the preserved replay unit and produce:
- a replayed decision result
- a replayed signal set
- a replayed enforcement expectation
- a verification verdict

If deterministic replay cannot be guaranteed, the runtime should explicitly record:
- the source of nondeterminism
- the affected replay scope
- the confidence of the replay verdict
- the operator-visible limitation note

## Replay Verdict Semantics
Each replay execution should produce one of the following verdicts:
- `match`: replay result is materially consistent with the original decision
- `drift`: replay completed but differs materially from the original decision
- `inconclusive`: replay could not establish a reliable comparison
- `invalid`: replay request or replay unit is incomplete or corrupted

## Drift Classification
When replay produces `drift`, the result should classify the difference using one or more of the following dimensions:
- input drift
- policy drift
- signal drift
- decision drift
- enforcement drift
- evidence drift

## Audit-Grade Replay Requirements
For escalated, blocked, or overridden decisions, replay records should preserve enough detail to:
- reconstruct the original decision context
- identify the original and replayed policy state
- compare original versus replayed signals
- compare original versus replayed actions
- explain the final replay verdict
- support operator and audit review

## Verification Gates
This phase is considered complete when:
- replay unit semantics are documented
- replay verdict semantics are documented
- drift classification is documented
- audit-grade replay minimums are documented
- roadmap generation and validation succeed

## Exit Criteria
- verification semantics are implementation-ready
- replay outcomes are unambiguous
- downstream phases can bind observability and enforcement validation to this contract
