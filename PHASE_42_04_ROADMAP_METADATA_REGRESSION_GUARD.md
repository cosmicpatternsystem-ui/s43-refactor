# PHASE 42.04 — Roadmap Metadata Regression Guard

Status: Recorded
Owner: Operations / Governance
Priority: High
Documentation Only: false
Depends On: PHASE_42_03_ROADMAP_METADATA_COMPLETENESS_AND_ENTERPRISE_READINESS_HARDENING.md

## Purpose

This phase adds regression coverage for roadmap metadata parsing so future changes cannot silently break header-based roadmap generation.

## Scope

- Add regression guard coverage for Markdown header metadata parsing.
- Verify `Status`, `Owner`, `Priority`, and `Documentation Only` are parsed from phase files.
- Verify canonical priority output remains stable.
- Verify the legacy roadmap metadata comment fallback remains supported.
- Verify body text containing `COMPLETE` does not override an explicit `Status: Recorded` header.

## Acceptance Criteria

- `scripts/test-roadmap.ps1` includes a regression guard for header-based roadmap metadata parsing.
- A fixture or temporary phase document proves `Status: Recorded` remains recorded even if the body contains the word `COMPLETE`.
- A fixture or temporary phase document proves `Owner`, `Priority`, and `Documentation Only` are extracted from headers.
- Priority values are normalized to the canonical roadmap values: `Critical`, `High`, `Medium`, `Low`.
- Legacy metadata comment fallback remains covered.
- `.\scripts\test-roadmap.ps1` passes.
- `git status --short` is clean after commit.

## Evidence

- `scripts/test-roadmap.ps1` regression guard output.
- `ROADMAP_CURRENT.json` remains stable after regeneration.
- Post-commit smoke test output confirms all roadmap gates pass.

## Risk

Without this guard, future edits to `scripts/update-roadmap.ps1` could reintroduce heuristic status detection or break metadata completeness without immediate detection.

## Rollback

Revert the test additions and remove this phase document if the guard introduces false positives or conflicts with the roadmap generation contract.


