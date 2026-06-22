# AI Decision Lifecycle Gate Audit Retention Enforcement Failure Mapping Contract

## Purpose
Define conservative failure mappings when retention enforcement readiness cannot be safely interpreted.

## Failure Conditions and Required Mapping

### Missing Definition
If retention scope, preservation rule, immutability expectation, or review-window basis is absent:
- exception category: `missing-definition`
- minimum outcome: `defer-enforcement`
- escalate to `block-promotion` if promotion reliance is requested

### Ambiguous Definition
If retention requirements permit materially inconsistent interpretations:
- exception category: `ambiguous-definition`
- minimum outcome: `defer-enforcement`
- escalate to `block-promotion` when ambiguity affects integrity, reviewability, or supersession status

### Evidence Deficiency
If retention evidence is partial, stale, unreachable, local-only, weakly attributable, or incomplete:
- exception category: `evidence-deficiency`
- minimum outcome: `defer-enforcement`
- escalate to `block-promotion` if evidence is missing, conflicting, or integrity-relevant

### Ownership Deficiency
If stewardship, reviewer authority, or governance accountability is undefined:
- exception category: `ownership-deficiency`
- minimum outcome: `defer-enforcement`
- escalate to `block-promotion` if no accountable reviewer can validate retention posture

### Secret-Bearing Artifact
If retained artifacts or supporting references contain secrets or sensitive material that violates policy:
- exception category: `evidence-deficiency`
- required outcome: `block-promotion`

### Conflicting Artifact State
If timestamps, integrity markers, identifiers, or supersession references conflict:
- exception category: `evidence-deficiency`
- required outcome: `block-promotion`

## Failure Handling Rules
1. Failures must be recorded explicitly and never inferred silently.
2. When multiple failures apply, the most conservative outcome prevails.
3. Temporary review convenience does not justify reducing a conservative failure outcome.
4. Exception approval cannot legitimize secret-bearing retention artifacts.
5. Remediation may change future mapping only after updated evidence is retained and reviewable.

## Required Failure Record Content
A failure mapping record should include:
- lifecycle decision identifier
- retention artifact or missing reference description
- failure condition
- exception category
- selected conservative outcome
- remediation expectation, if any
- accountable reviewer or governance owner
- timestamp
