# AI Decision Audit Evidence Standard

## Purpose

This standard defines minimum evidence expectations for AI-assisted decision records that may be reviewed by future governance, CI, or release enforcement workflows.

The standard is documentation-only and does not add automated evidence collection or runtime enforcement code.

## Evidence Requirements

A decision record should reference evidence for:

- Source input.
- AI output.
- Governing policy or contract.
- Operator disposition.
- Final status.
- Timestamp or lifecycle event.
- Review or approval when applicable.

Evidence should be explicit, reachable, and reviewable.

## Evidence Quality

Evidence should be:

- Traceable.
- Reviewable.
- Attributable.
- Consistent with the decision record.
- Free of secrets.
- Sufficient for audit reconstruction.

Evidence that is vague, missing, contradictory, or unreachable should not support promotion-ready classification.

## Governance States

Evidence may support the following outcomes:

- promotion-ready
- review-ready
- advisory-only
- blocked
- rejected
- invalid
- deferred-for-review

Promotion-ready status should require complete and reviewable evidence.

## Secret Handling

Evidence must not expose:

- Private keys.
- Seed phrases.
- API secrets.
- Authentication tokens.
- Session cookies.
- Unredacted credentials.

Sensitive content should be redacted or replaced with approved references.

## Non-Goals

This standard does not define:

- Runtime evidence capture.
- Automated prompt storage.
- Trading execution controls.
- Wallet permissions.
- Authentication logic.
- Model serving behavior.
- Secret storage implementation.

## Audit Expectations

An independent reviewer should be able to determine what evidence supports the decision, whether the evidence is complete, and whether the final governance status is justified.
