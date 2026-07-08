# Top-Level Readiness Gate

## Purpose
This document defines a strict professional readiness gate for:
- Veto
- Phoenix
- Shadow
- Recovery
- Safety
- Runtime resilience
- Observability
- State consistency

Passing this gate does not enable live trading.
Default state remains:

`SAFE-NO-TRADE`

## Non-Goals
This gate does not:
- modify runtime trading logic
- enable live trading
- activate recovery
- change auth/token/session behavior
- change exchange endpoints
- modify order execution logic

## Promotion Requirements
A branch is a top-level candidate only if:
1. working tree is clean
2. core python syntax checks pass
3. hardening tests pass when present
4. required roadmap docs exist or are explicitly reported missing
5. no runtime trading activation is introduced
6. no recovery activation is introduced

## Required Documents
- `docs/roadmap/PHASE8_PROGRESS.md`
- `docs/roadmap/PHASE8_RECOVERY_ACCEPTANCE.md`
- `docs/roadmap/PHASE8_RECOVERY_TOUCHPOINTS.md`
- `docs/roadmap/TOP_LEVEL_READINESS_GATE.md`

## Veto Conditions
- dirty working tree
- syntax failure
- failed hardening tests
- unreviewed runtime activation
- unreviewed recovery activation
- ambiguous safety state

## Final Rule
Top-level readiness is evidence-based, not claim-based.

Until stronger runtime evidence exists, the correct state remains:

`SAFE-NO-TRADE`
