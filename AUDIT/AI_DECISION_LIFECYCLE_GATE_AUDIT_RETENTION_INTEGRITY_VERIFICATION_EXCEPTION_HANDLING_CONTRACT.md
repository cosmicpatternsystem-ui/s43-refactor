# AI Decision Lifecycle Gate Audit Retention Integrity Verification Exception Handling Contract

## Purpose
Define how exceptions should be documented when retained audit artifact integrity verification controls are not fully ready for future enforcement.

## Exception Categories
- `missing-rule-definition`
- `ambiguous-rule-definition`
- `evidence-gap`
- `ownership-gap`
- `review-window-gap`
- `supersession-ambiguity`
- `integrity-signal-gap`
- `policy-incompatible-evidence`

## Required Exception Content
Each exception should include:
- exception category
- affected retained artifact or artifact class
- affected lifecycle decision or audit report reference, where applicable
- readiness category impact
- reason enforcement promotion is deferred or limited
- remediation owner
- evidence still required
- review window or next review condition
- timestamp

## Exception Handling Rules
1. Exceptions must be explicit and attributable.
2. Exceptions must not silently convert `not-ready` into `ready`.
3. Exceptions must not legitimize secret-bearing evidence.
4. Exceptions must identify the readiness dimension affected.
5. Exceptions must include a review condition or expiration expectation when applicable.
6. Exceptions must preserve traceability to the verification evidence record.

## Exception Impact Rules
1. Bounded evidence gaps may support `conditionally-ready`.
2. Missing artifact references require `not-ready`.
3. Secret-bearing evidence requires `not-ready`.
4. Conflicting integrity evidence requires `not-ready` until resolved.
5. Ownership ambiguity prevents `ready`.
6. Unbounded exceptions prevent enforcement promotion.

## Closure Requirements
An exception may be closed only when:
- required evidence has been added or corrected
- reviewer or governance owner has validated the update
- readiness category has been reassessed
- closure timestamp is recorded
- updated record remains secret-free
