# PROJECT_STATE

## Project

- Name: ASO-X
- Baseline branch: `main`
- Operating model: enterprise-grade, long-horizon, governance-enforced, audit-friendly

## Current Contract

This repository must be self-discoverable by a new assistant or operator without external explanation.

## Required Self-Discovery Outcome

A new session must be able to determine from repo artifacts:

- what the project is
- what baseline is accepted
- what controls are enforced
- what roadmap exists
- what next actions are recommended
- what artifacts are machine-validated
- what CI gates protect the system

## Repository Bootstrap Artifacts

- `AGENTS.md`
- `docs/ROADMAP.md`
- `docs/NEXT_ACTIONS.md`
- `docs/governance/GOVERNANCE_BASELINE.md`
- `docs/governance/LOCK_REGISTRY.json`
- `docs/governance/LOCK_SCHEMA.json`
- `.github/workflows/governance-enforcement.yml`
- `tools/project_status.py`
- `tests/test_governance_bootstrap.py`

## Operating Guarantees

- human-readable baseline
- machine-readable governance registry
- schema validation
- CI gate
- bootstrap status command
- anti-removal tests for critical bootstrap artifacts

## Persistence Intent

The system is designed for long-horizon continuity, safe handoff, and durable operational interpretation.

## Prohibited Regressions

- removing bootstrap artifacts
- removing machine-readable governance artifacts
- weakening CI validation
- reducing self-discovery quality
- replacing explicit repo evidence with implicit memory