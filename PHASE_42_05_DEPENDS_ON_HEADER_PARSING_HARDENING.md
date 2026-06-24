# Phase 42.05: Depends On Header Parsing Hardening

Status: Proposed
Documentation Only: Yes
Owner: Operations / Governance
Priority: High
Depends On: PHASE_42_04_ROADMAP_METADATA_REGRESSION_GUARD.md

## Objective

Harden roadmap metadata extraction so `Depends On:` headers in Markdown are
parsed consistently into the generated `depends_on` array in
`ROADMAP_CURRENT.json`.

## Problem Statement

Roadmap metadata parsing was hardened for `Status`, `Owner`, `Priority`, and
`Documentation Only`, but current evidence indicates `Depends On:` header values
are not yet reliably propagated end-to-end into generated roadmap metadata.

This leaves a gap in dependency integrity:

1. Markdown phase documents can declare dependencies that are silently ignored.
2. Regression coverage does not yet guarantee header-based dependency parsing.
3. Dependency validation can appear healthy while generation is incomplete.

## Scope

This phase covers:

1. Parsing `Depends On:` from Markdown headers.
2. Supporting both single-value and multi-value dependency declarations.
3. Normalizing separators, whitespace, and canonical phase filenames.
4. Ensuring generated `depends_on` arrays are populated in
   `ROADMAP_CURRENT.json`.
5. Adding regression tests so future parser changes cannot silently break this
   contract.

This phase does not cover:

1. Redesigning the roadmap schema.
2. Introducing non-header dependency formats beyond current metadata patterns.
3. Changing dependency semantics outside parsing and validation correctness.

## Proposed Hardening

### Parser Contract

The roadmap generator should:

1. Read `Depends On:` header values from Markdown phase documents.
2. Accept either:
   - a single dependency filename
   - multiple dependency filenames separated by commas
   - multiple dependency filenames separated by semicolons
3. Trim whitespace around each entry.
4. Drop empty tokens produced by malformed separators.
5. Preserve canonical `.md` phase document references.

### Validation Contract

The roadmap test suite should:

1. Verify that a phase with a `Depends On:` header produces a non-empty
   `depends_on` array.
2. Verify multiple dependencies are parsed correctly.
3. Verify invalid dependency references are rejected or surfaced as failures.
4. Prevent regressions where header parsing succeeds for scalar metadata but not
   dependency lists.

## Acceptance Criteria

1. A fixture or controlled roadmap phase using `Depends On:` produces the
   expected `depends_on` entries in `ROADMAP_CURRENT.json`.
2. Single dependency headers parse correctly.
3. Multi-dependency headers parse correctly.
4. Invalid dependency references fail validation or are explicitly surfaced by
   roadmap tests.
5. `.\scripts\test-roadmap.ps1` passes after generator and test updates.
6. Generated output is deterministic across repeated runs.

## Evidence Required

1. `git diff` showing generator hardening and regression tests.
2. Test output from `.\scripts\test-roadmap.ps1`.
3. Generated roadmap evidence confirming populated `depends_on` arrays from
   header-based metadata.

## Risks

1. Legacy roadmap documents may use inconsistent separators or spacing.
2. Mixed header and comment-block metadata could create precedence ambiguity if
   not defined clearly.
3. Validation may need to distinguish between omitted dependencies and malformed
   dependencies.

## Exit Condition

This phase is complete when header-based `Depends On:` metadata is proven to
flow correctly from Markdown source into generated roadmap artifacts with
regression coverage in place.
