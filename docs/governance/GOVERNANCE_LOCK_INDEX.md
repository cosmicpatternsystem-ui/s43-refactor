# Governance Lock Index

## Purpose

Provides an index for global governance lock artifacts.

## Required Controls

1. Primary lock matrix: GLOBAL_GOVERNANCE_LOCKS.md.
2. Machine registry: global-governance-locks.json.
3. Schema: global-governance-locks.schema.json.
4. Tests: tests/test_global_governance_locks.py.
5. CI gate: .github/workflows/global-governance-locks-gate.yml.

## Enforcement

1. Repository documentation
2. Machine-readable governance registry
3. Pytest validation
4. GitHub Actions gate
5. Pull request review

## Change Control

text
PR + required review + CI pass

## Retention

text
50y

## Failure Mode

text
block merge