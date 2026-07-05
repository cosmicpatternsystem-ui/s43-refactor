# AGENTS.md

## Identity

Project: ASO-X

This repository is a long-horizon financial-grade system. Treat durability, verifiability, and governance as first-class requirements.

## Source of Truth

- Source of truth is the repository only.
- Do not rely on chat memory if repository evidence exists.
- Prefer immutable history, explicit artifacts, and machine-readable state.

## Baseline

- Branch baseline: `main`
- The accepted baseline includes a governance system with machine-readable controls and CI enforcement.
- Continue from the repository's current verified state, not from obsolete chat context.

## Mandatory First Read In Every New Session

Read these in order before planning or editing:

1. `docs/PROJECT_STATE.md`
2. `docs/ROADMAP.md`
3. `docs/NEXT_ACTIONS.md`
4. `docs/governance/GOVERNANCE_BASELINE.md`
5. `docs/governance/LOCK_REGISTRY.json`
6. `docs/governance/LOCK_SCHEMA.json`
7. `.github/workflows/governance-enforcement.yml`
8. `tests/test_governance_bootstrap.py`
9. `tools/project_status.py`

## Session Start Contract

At the start of any new session, derive and summarize from repo evidence only:

- current baseline
- currently enforced controls
- next recommended actions
- hard constraints
- files and workflows that must not be weakened

If evidence is missing, say so explicitly and propose the minimum safe remediation.

## Non-Negotiable Rules

- Use repository evidence first.
- Do not speculate when repo evidence can be checked.
- Do not weaken governance, CI gates, schemas, registries, or audit trails.
- Preserve BOM-free UTF-8 LF.
- Use atomic writes where possible.
- Preserve cp1252-safe stdout for CLI status output.
- Keep changes safe for concurrent edits.
- Prefer additive, reviewable, PR-friendly changes.
- Do not silently rewrite project intent.

## Execution Policy

When asked what to do next, follow this priority order unless repo evidence says otherwise:

1. verify
2. harden
3. make tamper-evident
4. make operational
5. automate
6. document enforcement
7. extend safely

## Required Outputs

For analysis:
- concise status
- evidence paths
- risks
- next steps

For implementation:
- minimal blast radius
- test coverage
- workflow validation
- machine-readable artifact updates