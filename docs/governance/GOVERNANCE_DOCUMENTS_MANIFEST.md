# Governance Documents Manifest

This manifest is the canonical inventory for high-signal governance artifacts that must remain discoverable from the autonomous governance operations index and the repository entrypoint.

## Canonical Entrypoints

- `README.md`
- `docs/governance/AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md
`
- `docs/governance/GOVERNANCE_DOCUMENTS_MANIFEST.md`

## Critical Governance Artifacts
- Commercial Controls Enforcement Pack - `docs/strategy/COMMERCIAL_CONTROLS_ENFORCEMENT_PACK.md`
- `docs/strategy/COMMERCIAL_SOVEREIGNTY_REVENUE_PROTECTION_DOCTRINE.md`

| Artifact | Role | Enforcement |
| --- | --- | --- |
| `docs/governance/AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md` | Canonical autonomous governance routing surface | `tests/test_autonomous_governance_operations_index.py` |
| `docs/governance/AUTONOMOUS_FAILURE_HANDLING_RUNBOOK.md` | Failure classification and operator response path | `tests/test_autonomous_governance_operations_index.py` |
| `docs/governance/AUTONOMOUS_RECOVERY_AND_ROLLBACK_RUNBOOK.md` | Recovery, rollback, and post-failure stabilization path | `tests/test_autonomous_governance_operations_index.py` |
| `docs/governance/AUTONOMOUS_MERGE_SAFETY_CHECKLIST.md` | Merge readiness, safety checks, and autonomous merge guardrails | `tests/test_autonomous_governance_operations_index.py` |
| `README.md` | Top-level repository entrypoint for governance discovery | `tests/test_readme_governance_entrypoint.py` |

## Contract

Every artifact listed in Critical Governance Artifacts must satisfy all of these rules:

- the artifact path must exist in the repository
- the artifact path must be listed in this manifest
- critical autonomous governance artifacts must be linked from `docs/governance/AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md`
- the autonomous governance operations index must be linked from `README.md`
- enforcement tests must fail when canonical routing drifts
- docs/strategy/STRATEGIC_CONTROL_PLANE.md
- docs/strategy/PROJECT_OBJECTIVES.md
- docs/strategy/CANONICAL_ROADMAP.md
- docs/strategy/FIFTY_YEAR_DURABILITY_DOCTRINE.md
- docs/strategy/MONETIZATION_AND_MARKET_DOCTRINE.md
- docs/strategy/AUTONOMOUS_CONTINUITY_GUIDE.md
- docs/strategy/ANTI_OBSOLESCENCE_POLICY.md
- docs/strategy/PORTABILITY_AND_PLATFORM_INDEPENDENCE.md
- docs/strategy/PRODUCT_IDENTITY_AND_DIFFERENTIATION.md
### Strategy

- `docs/strategy/TOP_LEVEL_COMMERCIAL_OPERATING_DOCTRINE.md` - top-level commercial operating doctrine defining revenue quality, trust-based positioning, pricing discipline, customer selection, and commercial governance
- `docs/strategy/GLOBAL_COMMERCIAL_HARDENING_ADDENDUM.md` - Global commercial hardening addendum.
| docs/strategy/GLOBAL_COMMERCIAL_RESILIENCE_FRAMEWORK.md | Global commercial resilience framework governing pricing discipline, cash protection, commitment integrity, counterparty fitness, and exception control. |
| docs/strategy/COMMERCIAL_AUTHORITY_MATRIX.md | Commercial Authority Matrix governing commercial decision rights for discounts, margin floors, concessions, payment terms, delivery promises, escalation, and NO-GO conditions. |
