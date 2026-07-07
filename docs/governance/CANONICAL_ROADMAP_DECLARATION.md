# CANONICAL ROADMAP DECLARATION

Status: Active
Scope: ASO-X / s43-refactor
Canonical machine-readable roadmap state: `ROADMAP_CURRENT.json`
Canonical human-readable roadmap: `ROADMAP_CANONICAL.md`
Derivative roadmap views: `ROADMAP.md`, `docs/ROADMAP.md`
Traceability index: `docs/roadmap/roadmap.index.json`
Governance class: 50-year durable roadmap governance
Baseline date: 2026-07-05
Baseline state: CLOSED / MERGED / VERIFIED / BASELINE-RECORDED / CLEAN

## Canonical Sources

- Machine-readable active roadmap state: `ROADMAP_CURRENT.json`
- Human-readable canonical roadmap: `ROADMAP_CANONICAL.md`
- Derivative roadmap views: `ROADMAP.md`, `docs/ROADMAP.md`
- Non-prevailing traceability index: `docs/roadmap/roadmap.index.json`

## Governance Rules

1. `ROADMAP_CURRENT.json` is the active machine-readable roadmap state.
2. `ROADMAP_CANONICAL.md` is the canonical human-readable roadmap.
3. `ROADMAP.md` and `docs/ROADMAP.md` are derivative views and must never override canonical roadmap truth.
4. `docs/roadmap/roadmap.index.json` is a traceability index and must not declare independent roadmap authority.
5. Durable roadmap requirements must have stable IDs.
6. Requirement IDs must never be reused after retirement.
7. Active governance requirements must be CI-validatable where applicable.
8. Governance artifacts must remain portable and long-lived.
9. Repository state is authoritative over prior conversation state.
10. Any future promotion of a new roadmap source requires an explicit governance PR updating `REPOSITORY_TRUTH.md`, `SOURCE_OF_TRUTH_HIERARCHY.md`, validators, and CI gates in the same change set.

