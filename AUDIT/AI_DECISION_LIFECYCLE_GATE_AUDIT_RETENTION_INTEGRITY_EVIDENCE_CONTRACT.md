# AI Decision Lifecycle Gate Audit Retention Integrity Evidence Contract

## Contract Statement
Any claim that a retained AI decision lifecycle gate audit artifact is suitable for integrity verification must be supported by explicit, attributable, and reviewable evidence.

## Required Evidence Elements
A minimally acceptable verification evidence set should include:
- retained artifact reference
- artifact identifier
- integrity marker, hash, or documented equivalent control
- retention timestamp or preserved creation/retention timing signal
- lifecycle decision reference or audit report reference
- schema, format, or version context when needed for interpretation
- reviewer or governance actor identity
- secret-free confirmation

## Supplemental Evidence Elements
Where applicable, verification evidence should also include:
- supersession reference
- current versus stale/expired/historical status
- storage location class
- retrieval or review timestamp
- approved exception reference
- prior verification reference

## Contract Requirements
1. Evidence must be sufficient for an independent reviewer to understand why a verification posture was assigned.
2. Evidence must not rely on undocumented local state, memory, or implicit knowledge.
3. Evidence must remain attributable to a specific artifact and lifecycle context.
4. Evidence must remain policy-compatible and secret-free.
5. If required evidence is absent, the artifact cannot be treated as `verification-ready`.

## Evidence Quality Rules
1. Complete, attributable, and reviewable evidence may support `verification-ready`.
2. Bounded evidence gaps with explicit review may support `verification-ready-with-review`.
3. Partial, stale, weakly attributable, or unreachable evidence should support `verification-deferred`.
4. Missing, conflicting, or secret-bearing evidence must support `verification-failed`.

## Minimal Decision Record
A compliant verification evidence decision record should include:
- retained artifact reference
- verification evidence summary
- assigned verification posture
- failure or exception reference, if applicable
- reviewer or governance owner
- timestamp
