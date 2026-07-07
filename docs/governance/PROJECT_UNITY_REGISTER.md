# PROJECT UNITY REGISTER

## Status

- Authority: Active
- Scope: Repository-wide
- Purpose: Single register for project-wide unity between governance, contracts, automation, evidence, and accepted branch state

## Unity Surfaces

| Surface | Authority | Required State |
| --- | --- | --- |
| Governance | `docs/governance/` | Policy is explicit and durable |
| Roadmap | `docs/roadmap/` | Direction is sequenced and reviewable |
| Automation | `asoctl.py` | Operational checks are executable |
| Artifacts | `artifacts/audits/` | Audit evidence is retained |
| Integration | GitHub pull requests | Accepted change is reviewed |
| Accepted truth | `main` | Repository state is synchronized and clean |

## Current Unified Spine

| Domain | Baseline |
| --- | --- |
| Source of truth | Repository only |
| Change flow | Pull request into `main` |
| Merge safety | Safe Merge Automation |
| Verification command | `python asoctl.py safe-merge verify` |
| Artifact retention | Required for audit-relevant outputs |
| Encoding | UTF-8 without BOM |
| Line endings | LF |
| Write discipline | Atomic writes |
| Console discipline | cp1252-safe stdout |
| Durability target | 50 years |
| Commercial posture | Real-money resilient |

## Drift Conditions

The project is drifting if any condition is true:

- Governance says something automation does not enforce or acknowledge.
- Automation emits evidence that is not retained when retention is required.
- Required checks differ from repository contracts.
- `main` does not represent the accepted project state.
- Branch cleanup remains incomplete after merge.
- Durable text files contain BOM or CRLF.
- Critical operational rules exist only in conversation.
- Manual process is required repeatedly but not represented in repository truth.

## Recovery Conditions

The project returns to unity when:

- The missing policy is committed.
- The missing contract is committed.
- The missing automation is committed.
- The missing evidence path is committed or generated.
- The required verification passes.
- `main` is synchronized with `origin/main`.
- The working tree is clean.
- Obsolete branches are pruned.

## Commercial Rule

If the project cannot prove its state from repository truth and retained evidence, the state is not commercially strong enough.
