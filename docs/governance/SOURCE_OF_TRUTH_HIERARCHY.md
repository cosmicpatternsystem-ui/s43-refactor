# Source of Truth Hierarchy

This document defines precedence when project artifacts disagree.

## Highest Authority

1. `docs/governance/GOAL_CONSTITUTION.md`
2. `repo/contracts/PROJECT_CONSTITUTION.yaml`
3. `repo/contracts/CANONICAL_SOURCES.yaml`
4. `docs/governance/REPOSITORY_TRUTH.md`
5. `docs/governance/SOURCE_OF_TRUTH_HIERARCHY.md`
6. `docs/governance/ROADMAP_CONSTITUTION.md`
7. `PROJECT_CHARTER.md`
8. `ROADMAP_CURRENT.json`
9. `ROADMAP_CANONICAL.md`
10. `PROJECT_STATE.md`
11. `POLICY_MATRIX.md`
12. `ROADMAP.md`
13. `docs/ROADMAP.md`
14. `docs/roadmap/roadmap.index.json`
15. `docs/governance/POLICY_MATRIX.md`
16. `docs/governance/COMPATIBILITY_CONTRACT.md`
17. `docs/OPERATIONS_RUNBOOK.md`
18. `docs/COMMERCIAL_MODEL.md`
19. `docs/governance/DECISION_LOG.md`
20. implementation code
21. generated artifacts
22. chat transcripts and external notes

## Conflict Rule

When two artifacts conflict, the higher-ranked artifact controls until a PR updates the lower-ranked artifact or records an explicit decision.

## Repository Rule

Repository files outrank chat memory, local memory, screenshots, informal notes, and undocumented assumptions.

## Machine-Readable Rule

When a human-readable document and its machine-readable contract disagree, the machine-readable contract controls for automation, but the conflict must be fixed.

## Roadmap Rule

`ROADMAP_CURRENT.json` is the active machine-readable roadmap state.

`ROADMAP_CANONICAL.md` is the canonical human-readable roadmap.

`ROADMAP.md`, `docs/ROADMAP.md`, and `docs/roadmap/roadmap.index.json` are derivative, index, or public-facing views. They must remain synchronized with canonical roadmap truth but must never override `ROADMAP_CURRENT.json` or `ROADMAP_CANONICAL.md`.

`repo/roadmap/roadmap.yaml` and `ROADMAP/ROADMAP_STATE.json` are non-authoritative unless explicitly promoted by a future governance PR and reflected in this hierarchy.

## Decision Rule

Major direction changes require an entry in `docs/governance/DECISION_LOG.md` or a successor decision mechanism declared in `repo/contracts/PROJECT_CONSTITUTION.yaml`.

## Safety Rule

If precedence cannot be resolved, no irreversible change should be made until the source-of-truth hierarchy is updated.
