# GOVERNANCE_BASELINE

## Purpose

This repository contains a governance baseline intended to be durable, self-discoverable, and enforceable.

## Baseline Principles

- machine-readable governance
- schema validation
- CI enforcement
- anti-removal protection for bootstrap artifacts
- explicit roadmap and next-action continuity
- safe continuation by new sessions using repo evidence only

## Required Governance Files

- `docs/governance/LOCK_REGISTRY.json`
- `docs/governance/LOCK_SCHEMA.json`

## Required Continuity Files

- `AGENTS.md`
- `docs/PROJECT_STATE.md`
- `docs/ROADMAP.md`
- `docs/NEXT_ACTIONS.md`

## Required Enforcement Files

- `.github/workflows/governance-enforcement.yml`
- `tests/test_governance_bootstrap.py`
- `tools/project_status.py`

## Governance Decision Rule

If a future change conflicts with continuity, auditability, or enforceability, prefer the safer and more explicit path.