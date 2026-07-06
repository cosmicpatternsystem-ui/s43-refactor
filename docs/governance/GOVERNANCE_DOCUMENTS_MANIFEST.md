# Governance Documents Manifest

This manifest is the canonical inventory for high-signal governance artifacts that must remain discoverable from the autonomous governance operations index and the repository entrypoint.

## Canonical Entrypoints

- `README.md`
- `docs/governance/AUTONOMOUS_GOVERNANCE_OPERATIONS_INDEX.md
`
- `docs/governance/GOVERNANCE_DOCUMENTS_MANIFEST.md`

## Critical Governance Artifacts

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