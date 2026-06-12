# Phase 13 Governance Integration Checkpoint

## Status

Phase 13 started from the completed Phase 12 merge point.

Base branch:

- hardening/phase10-post-freeze-local-edits

Starting tag:

- phase12-merged-governance-risk-guard

## Phase 13 Objective

Phase 13 focuses on governance integration and enforcement readiness.

The goal is to move from isolated RiskGuard validation toward a durable operational governance layer that can be safely integrated into project workflows.

## Scope

Phase 13 should address:

1. Integration mapping
   - Identify where governance/risk_guard.py should be invoked.
   - Identify entrypoints that require governance checks.
   - Avoid unsafe behavioral changes until tests exist.

2. Enforcement boundaries
   - Define dry-run versus enforce mode.
   - Ensure governance decisions remain explicit and auditable.
   - Preserve fail-closed behavior for invalid or unsafe inputs.

3. Test expansion
   - Add integration-level tests around governance invocation.
   - Verify decision contract stability.
   - Verify no silent bypass paths exist.

4. Documentation
   - Document operational use of RiskGuard.
   - Document expected GovernanceDecision fields and severity semantics.
   - Document migration path toward enforced governance.

## Non-Goals

Phase 13 does not directly introduce live trading, wallet movement, key handling, or production execution.

Any change that could affect funds, secrets, or live execution must remain blocked unless explicitly covered by safety protocol and tests.

## Initial Safety Requirements

- Repository must remain clean before each major step.
- Tests must pass before every commit.
- Governance changes must be documented.
- No direct bypass of GovernanceDecision contract.
- No weakening of Phase 12 validation behavior.

## Initial Validation Commands

Recommended baseline validation:
```powershell
python -m pytest -q

or:

powershell
py -m pytest -q

## Phase 13 Working Branch

text
phase13-governance-integration

## Completion Criteria Draft

Phase 13 can be considered complete when:

- Governance integration points are mapped.
- Enforcement/dry-run behavior is documented.
- Integration tests are added.
- Full test suite passes.
- Durable checkpoint documentation is committed.
- A PR is opened and squash-merged into the default branch.
