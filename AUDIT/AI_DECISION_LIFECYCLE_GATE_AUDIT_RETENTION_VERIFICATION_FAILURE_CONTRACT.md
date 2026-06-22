# AI Decision Lifecycle Gate Audit Retention Verification Failure Contract

## Purpose
Define conservative failure handling when retained audit artifact integrity cannot be established with sufficient confidence.

## Failure Conditions

### Missing Integrity Signal
If no integrity marker, hash-equivalent, or documented integrity control can be identified:
- minimum posture: `verification-deferred`
- escalate to `verification-failed` when integrity reliance is requested

### Missing Artifact Reference
If the retained artifact cannot be uniquely identified or referenced:
- required posture: `verification-failed`

### Missing Timing or Version Context
If retention timing, schema, or version context is absent and materially affects interpretation:
- minimum posture: `verification-deferred`
- escalate to `verification-failed` when reproducibility is not possible

### Conflicting Verification Signals
If identifiers, timestamps, integrity markers, supersession references, or status indicators conflict:
- required posture: `verification-failed`

### Unreachable or Local-Only Evidence
If verification depends on evidence that is unreachable, local-only, or not reviewable by governance:
- minimum posture: `verification-deferred`
- escalate to `verification-failed` when no compensating attributable evidence exists

### Secret-Bearing Evidence
If the evidence set includes secrets or policy-incompatible sensitive material:
- required posture: `verification-failed`

### Ownership or Reviewer Ambiguity
If no accountable reviewer or governance owner can validate the evidence:
- minimum posture: `verification-deferred`
- escalate to `verification-failed` when verification approval is being asserted

## Failure Handling Rules
1. Failure conditions must be recorded explicitly.
2. Temporary convenience does not justify downgrading a conservative failure posture.
3. Exceptions cannot legitimize secret-bearing verification evidence.
4. Remediation may change posture only after updated evidence becomes attributable and reviewable.
5. When multiple failures apply, the most conservative posture prevails.

## Required Failure Record Content
A verification failure record should include:
- retained artifact reference or missing-reference description
- lifecycle decision or audit report reference
- failure condition
- assigned verification posture
- remediation expectation, if any
- accountable reviewer or governance owner
- timestamp
