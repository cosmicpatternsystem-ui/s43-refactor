# AI Decision Evidence Contract

## Purpose

This contract defines the evidence expected for AI-assisted recommendations, classifications, and operational decision support.

The contract is documentation-only and does not add runtime behavior.

## Evidence Requirements

An AI decision evidence bundle should include:

- Source input reference.
- AI output reference.
- Decision category.
- Governing policy or contract.
- Operator disposition.
- Supporting context.
- Limitation or uncertainty note when available.
- Final status.
- Timestamp.

## Evidence Quality Rules

Evidence should be:

- Specific enough to review.
- Durable enough to survive later audit.
- Free of secrets and private credentials.
- Linked to a decision record.
- Associated with a responsible owner or role.
- Consistent with roadmap governance expectations.

## Incomplete Evidence

Evidence is incomplete when:

- The AI output is recorded without input context.
- The operator disposition is missing.
- The governing policy is not identified.
- The final status is ambiguous.
- Supporting evidence cannot be located.
- The record contains secrets or private credentials.

Incomplete evidence should prevent promotion to accepted or enforced status.

## Secret Handling

Evidence bundles must not include:

- Private keys.
- Wallet seed phrases.
- API secrets.
- Authentication tokens.
- Session cookies.
- Unredacted credentials.

Any evidence requiring sensitive context must use redacted references or approved secret-handling procedures.

## Future Enforcement Direction

Future phases may enforce this contract through:

- CI validation.
- Audit evidence checks.
- Structured decision record schemas.
- Roadmap gate integration.
- Release readiness checks.

## Acceptance Conditions

An AI decision evidence bundle is acceptable when a reviewer can determine what was recommended, why it was reviewed, who made the final decision, and what evidence supports that decision.
