# AI Decision Lifecycle Gate Audit Retention Integrity Verification Enforcement Failure Mapping Contract

## Purpose
Define failure scenarios that constrain or determine conservative enforcement mapping outcomes.

## Failure Categories
- `missing-rule-definition`
- `missing-artifact-reference`
- `missing-integrity-context`
- `conflicting-verification-evidence`
- `unreachable-evidence`
- `local-only-evidence`
- `ownership-ambiguity`
- `review-window-gap`
- `policy-incompatible-evidence`
- `secret-bearing-evidence`

## Failure Mapping Rules
1. `secret-bearing-evidence` => `block-promotion`
2. `policy-incompatible-evidence` => `block-promotion`
3. `conflicting-verification-evidence` => `block-promotion`
4. `missing-artifact-reference` => `not-ready` and at least `defer-enforcement`
5. `missing-integrity-context` => `conditionally-ready` or `not-ready` depending on severity
6. `unreachable-evidence` => at least `defer-enforcement`
7. `local-only-evidence` => at least `defer-enforcement`
8. `ownership-ambiguity` => no `allow`
9. `review-window-gap` => no `allow-with-review`
10. Multiple simultaneous failures may require escalation to `block-promotion`

## Required Failure Record
A failure mapping record should include:
- failure category
- affected artifact or assessment reference
- readiness impact
- minimum outcome constraint
- remediation owner
- reassessment condition
- timestamp

## Closure Expectations
A mapped failure may be cleared only when:
- the underlying deficiency is corrected
- evidence is re-reviewed
- mapping outcome is reassessed
- traceable closure is recorded
- resulting state remains secret-free and policy-compatible
