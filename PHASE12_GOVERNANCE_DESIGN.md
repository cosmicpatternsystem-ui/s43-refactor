# Phase 12 Governance Design

## Mission

Phase 12 defines a safe, professional, testable governance architecture for future runtime protection features.

This phase must transform useful legacy ideas into clean, isolated, documented, and testable components without repeating the direct-injection problems observed in earlier Phase 11 experiments.

## Current Baseline

Phase 12 starts from the durable Phase 11 checkpoint:

- Branch: `phase12-governance-design`
- Parent checkpoint: `phase11-durable-checkpoint`
- Stable reference branch: `phase11-readiness`
- Legacy reference: `legacy_reference/11029_legacy_reference.py`

The Phase 11 readiness state is preserved and must remain recoverable.

## Non-Negotiable Safety Rules

- Do not inject governance checks directly into `s43.py`.
- Do not import or execute `legacy_reference/11029_legacy_reference.py` directly.
- Do not activate enforcement logic before tests, dry-run, and explicit activation gates exist.
- Do not mix experimental governance logic with production runtime paths.
- Do not treat legacy code as production-ready.
- Do not bypass central runtime control points.
- Do not add hidden side effects, automatic blocking, or silent behavior changes.

## Legacy Extraction Policy

Legacy code may be used only as a reference source.

Any useful idea from the legacy reference must go through this process:

1. Identify the capability.
2. Document its intended purpose.
3. Extract the concept, not the raw implementation.
4. Design a clean interface.
5. Implement it in an isolated module.
6. Add unit tests.
7. Add dry-run behavior.
8. Add observability and structured result reporting.
9. Connect only through a central hook.
10. Enable enforcement only after explicit approval.

## Candidate Capabilities

Potential candidates from the legacy reference include:

- Capital protection logic.
- Wallet cycle guard behavior.
- Kill-switch concepts.
- Risk sentinel improvements.
- Runtime governance checks.
- Exposure limits.
- Cooldown rules.
- Emergency pause concepts.

These are candidates only, not approved production features.

## Proposed Architecture

Phase 12 should use isolated modules and explicit contracts.

Suggested future structure:
```text
s43_governance.py
governance/
  __init__.py
  contracts.py
  decisions.py
  dry_run.py
  capital_guard.py
  wallet_cycle_guard.py
  risk_sentinel.py
  runtime_hook.py
tests/
  test_governance_contracts.py
  test_dry_run.py
  test_capital_guard.py
  test_wallet_cycle_guard.py

This structure is a proposal and should be introduced gradually.

## Governance Decision Contract

Every governance check should return a structured decision instead of directly mutating runtime behavior.

Suggested decision fields:

- `allowed`
- `severity`
- `reason`
- `rule_id`
- `mode`
- `metadata`
- `timestamp`

Governance checks should not directly stop execution unless enforcement mode is explicitly enabled.

## Dry-Run Contract

Dry-run mode is mandatory before enforcement.

In dry-run mode, governance logic may:

- evaluate risk
- return warnings
- produce structured decisions
- log proposed actions
- collect metrics

In dry-run mode, governance logic must not:

- block execution
- alter wallet state
- alter capital state
- change trading behavior
- trigger emergency shutdown
- modify `s43.py` behavior silently

## Central Runtime Hook

Any future integration with `s43.py` must happen through a minimal, explicit, central runtime hook.

The hook must:

- be easy to find
- be easy to disable
- support dry-run mode
- support enforcement mode only by configuration
- return structured decisions
- avoid scattered inline checks
- avoid hidden imports
- avoid repeated injection patterns

No direct Phase 11-style scattered governance calls are allowed.

## Activation Gates

A governance capability may move toward enforcement only when all gates pass:

1. Design documented.
2. Interface defined.
3. Unit tests added.
4. Dry-run behavior implemented.
5. Failure behavior documented.
6. Rollback path documented.
7. Runtime hook reviewed.
8. No direct legacy import.
9. No direct scattered injection into `s43.py`.
10. Explicit approval recorded.

## Testing Strategy

Phase 12 must prioritize tests before runtime activation.

Required test categories:

- contract tests
- dry-run tests
- edge-case tests
- no-side-effect tests
- rollback tests
- integration boundary tests

Tests should verify that dry-run mode never changes runtime behavior.

## Observability

Governance decisions should be inspectable.

Future implementation should support:

- structured decision objects
- clear rule IDs
- explicit severity levels
- reason messages
- optional metadata
- dry-run reporting

Silent blocking or invisible mutation is not acceptable.

## Rollback Plan

Every Phase 12 runtime integration must be reversible.

Rollback requirements:

- central hook can be disabled
- enforcement mode can be turned off
- dry-run mode can remain available
- no irreversible migration is required
- stable Phase 11 checkpoint remains available through tags

Relevant tags:

- `phase11-readiness-freeze`
- `phase11-durable-checkpoint`

## Definition of Done

Phase 12 design work is complete when:

- architecture is documented
- extraction policy is documented
- safety rules are documented
- dry-run contract is documented
- activation gates are documented
- test strategy is documented
- no runtime behavior has changed without review
- future implementation tasks are clear and isolated

## Immediate Next Steps

1. Review this design document.
2. Create a capability inventory from `legacy_reference/11029_legacy_reference.py`.
3. Select one low-risk capability for extraction design.
4. Define its contract before implementation.
5. Add tests before runtime integration.
