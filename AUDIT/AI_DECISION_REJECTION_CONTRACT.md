# AI Decision Rejection Contract

## Purpose

This contract defines the conditions under which an AI-assisted decision record should be rejected, blocked, or downgraded.

The contract is documentation-only and does not introduce automated rejection logic.

## Rejection Conditions

A decision record should be rejected or blocked when any of the following applies:

- Source input reference is missing.
- AI output reference is missing.
- Governing policy or contract is missing.
- Operator disposition is missing.
- Evidence is absent or non-reviewable.
- Final status is undefined or contradictory.
- Traceability is insufficient for audit reconstruction.
- The record includes secrets, credentials, or private sensitive material.

## Downgrade Conditions

A record should be downgraded to advisory-only when:

- Recommendation exists but evidence is incomplete.
- Evidence exists but operator disposition is pending.
- Traceability exists but final status is deferred.
- Supporting policy references are incomplete but under remediation.

Downgrade should preserve reviewability without allowing promotion.

## Rejection Outcomes

Recommended governance outcomes include:

- blocked
- rejected
- advisory-only
- invalid
- deferred-for-review

A future implementation phase may map these outcomes to CI failures or release gates.

## Secret Handling

Rejected records must not be preserved in a form that exposes:

- Private keys.
- Seed phrases.
- API secrets.
- Authentication tokens.
- Session cookies.
- Unredacted credentials.

Sensitive content should be redacted or replaced with approved references.

## Audit Expectations

Audit review should be able to determine why the record was rejected, blocked, or downgraded, and what remediation is required before resubmission.
