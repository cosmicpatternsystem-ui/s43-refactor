# Source of Truth Hierarchy

This document defines precedence when project artifacts disagree.

## Highest Authority

1. `docs/governance/GOAL_CONSTITUTION.md`
2. `repo/contracts/PROJECT_CONSTITUTION.yaml`
3. `repo/contracts/CANONICAL_SOURCES.yaml`
4. `PROJECT_CHARTER.md`
5. `repo/roadmap/roadmap.yaml`
6. `docs/ROADMAP.md`
7. `docs/governance/POLICY_MATRIX.md`
8. `docs/governance/COMPATIBILITY_CONTRACT.md`
9. `docs/OPERATIONS_RUNBOOK.md`
10. `docs/COMMERCIAL_MODEL.md`
11. `docs/governance/DECISION_LOG.md`
12. implementation code
13. generated artifacts
14. chat transcripts and external notes

## Conflict Rule

When two artifacts conflict, the higher-ranked artifact controls until a PR updates the lower-ranked artifact or records an explicit decision.

## Repository Rule

Repository files outrank chat memory, local memory, screenshots, informal notes, and undocumented assumptions.

## Machine-Readable Rule

When a human-readable document and its machine-readable contract disagree, the machine-readable contract controls for automation, but the conflict must be fixed.

## Roadmap Rule

`repo/roadmap/roadmap.yaml` is the canonical roadmap source.

`docs/ROADMAP.md` is the human-readable roadmap view and must remain synchronized with the roadmap source.

## Decision Rule

Major direction changes require an entry in `docs/governance/DECISION_LOG.md` or a successor decision mechanism declared in `repo/contracts/PROJECT_CONSTITUTION.yaml`.

## Safety Rule

If precedence cannot be resolved, no irreversible change should be made until the source-of-truth hierarchy is updated.
