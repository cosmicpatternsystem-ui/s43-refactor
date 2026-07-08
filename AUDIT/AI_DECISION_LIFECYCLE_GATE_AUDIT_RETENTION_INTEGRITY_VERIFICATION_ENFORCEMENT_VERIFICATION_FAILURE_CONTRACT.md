# AI Decision Lifecycle Gate Audit Retention Integrity Verification Enforcement Verification Failure Contract

## Purpose
Define failure conditions that prevent verification of future integrity verification enforcement outcomes.

## Failure Categories
- `missing-outcome-reference`
- `missing-readiness-reference`
- `missing-evidence-posture-reference`
- `missing-exception-context`
- `unreachable-evidence`
- `local-only-evidence`
- `ownership-ambiguity`
- `review-window-gap`
- `conflicting-verification-signals`
- `policy-incompatible-evidence`
- `secret-bearing-evidence`

## Failure Rules
1. `secret-bearing-evidence` => `verification-failed`
2. `policy-incompatible-evidence` => `verification-failed`
3. `conflicting-verification-signals` => `verification-failed`
4. `missing-outcome-reference` => `verification-failed`
5. `missing-readiness-reference` => `verification-deferred` or `verification-failed`
6. `missing-evidence-posture-reference` => `verification-deferred` or `verification-failed`
7. `unreachable-evidence` => at least `verification-deferred`
8. `local-only-evidence` => at least `verification-deferred`
9. `ownership-ambiguity` => no verified approval outcome
10. `review-window-gap` => no `verification-ready-with-review`

## Required Failure Record
A failure record should include:
- failure category
- affected reference
- verification impact
- minimum posture constraint
- remediation owner
- reassessment condition
- timestamp

## Closure Expectations
A verification failure may be cleared only when:
- the underlying deficiency is corrected
- evidence is re-reviewed
- the verification posture is reassessed
- traceable closure is recorded
- the resulting state remains secret-free and policy-compatible
