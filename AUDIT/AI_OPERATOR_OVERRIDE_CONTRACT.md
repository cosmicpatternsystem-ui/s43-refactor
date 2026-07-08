# AI Operator Override Contract

## Purpose

This contract defines governance requirements for human override, rejection, or modification of AI-assisted recommendations.

The contract is documentation-only and does not implement runtime override logic.

## Override Principle

AI-assisted recommendations must remain subject to human operator review unless a future phase explicitly authorizes a narrower automated pathway with enforceable controls.

The operator must be able to:

- Accept the recommendation.
- Reject the recommendation.
- Override the recommendation.
- Defer the recommendation.
- Request additional evidence.

## Override Record

An override record should include:

- Override identifier.
- Related AI decision identifier.
- Original AI recommendation.
- Operator disposition.
- Override reason.
- Supporting evidence.
- Responsible role.
- Timestamp.
- Final status.

## Override Reasons

Acceptable override reason categories may include:

- insufficient-evidence
- stale-input
- policy-conflict
- operational-risk
- commercial-risk
- security-risk
- release-risk
- manual-review-required
- other-documented-reason

Free-form details may be attached when required, but the category should remain structured.

## Governance Rules

Operator overrides should be:

- Recorded before final disposition is promoted.
- Linked to supporting evidence.
- Reviewable by audit.
- Free of secrets and credentials.
- Consistent with active governance contracts.

An override without evidence should not be treated as final approval.

## Non-Goals

This contract does not define:

- Runtime permission models.
- UI controls.
- Authentication mechanisms.
- Trading automation.
- Wallet authorization.
- Secret storage.
- Model execution.

## Future Enforcement Direction

Future phases may introduce automated checks to ensure AI recommendations cannot be promoted without explicit operator disposition and evidence.
