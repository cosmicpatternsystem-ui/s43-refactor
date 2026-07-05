# Project State

Last updated: 2026-07-05

## Repository

- Repository: cosmicpatternsystem-ui/s43-refactor
- URL: https://github.com/cosmicpatternsystem-ui/s43-refactor

## Current Stable Branch

- main

## Current Local Main HEAD

- Short: b02643d Record project state after artifact retention audit merge (#223)
- Full SHA: b02643d8736cfc223c63efc5a235bcc94edb32d1

## Recently Completed / Confirmed

- PR #223: Record project state after artifact retention audit merge
  - GitHub state: MERGED
  - Merged at: 2026-07-05T11:09:40Z
  - Merge commit reported by GitHub: b02643d8736cfc223c63efc5a235bcc94edb32d1
  - URL: https://github.com/cosmicpatternsystem-ui/s43-refactor/pull/223
- PR #222: Fix evidence record schema test indentation and remove schema BOM
- PR #218: Add P2.11 artifact retention scheduled audit
  - GitHub state: MERGED
  - Merged at: 2026-07-05T09:26:29Z
  - Merge commit reported by GitHub: 27f6a366e7688abb3c945ea702fdbd889ae3fc5a
  - URL: https://github.com/cosmicpatternsystem-ui/s43-refactor/pull/218

## Current Operating Rules

- Source of truth is the repository.
- GitHub PR state and repository docs override chat memory.
- Decisions must follow docs/ROADMAP.md and docs/PROJECT_STATE.md when those files exist.
- CI checks must pass before merge.
- Work should proceed by pull request unless explicitly documented otherwise.
- Files should be UTF-8 without BOM and use LF line endings where practical.
- Workflows that invoke pytest must install pytest or use a dependency setup that provides it.
- Local validation is useful, but GitHub Actions is authoritative for merge readiness.

## Validation Baseline

- GitHub Actions checks must pass.
- Relevant focused pytest targets must pass locally or in CI.
- Artifact retention evidence files must be generated and retained when expected.
- Schema files must remain parseable and BOM-free where required.
- Main branch must remain fast-forward syncable from origin/main.

## Current Known Follow-ups

1. Verify artifact retention scheduled audit behavior on main after PR #218.
2. Ensure every workflow that invokes pytest has dependency setup coverage.
3. Review docs/ROADMAP.md for the next prioritized P item.
4. Keep this file updated after every merged PR.
