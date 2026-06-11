# CP003-B Integration Insertion Map

## Status

- Phase: CP003-B
- Document type: Integration Insertion Map
- Branch: cp003-b-integration-planning
- Base tag: s43-cp003-a-locked
- Planning start tag: s43-cp003-b-start
- Charter tag: s43-cp003-b-charter-v1
- Runtime integration: UNAUTHORIZED
- Live trading: UNAUTHORIZED
- Baseline executable mutation: UNAUTHORIZED

## Purpose

This document defines the planning map for possible future integration between the existing S43 baseline and the CP003 scaffold modules.

This document does not authorize runtime integration.

Its purpose is to identify protected files, read-only inspection targets, allowed planning artifacts, and the minimum requirements before any future executable mutation can be proposed.

## Current Baseline Boundary

The current executable baseline remains locked at:

- Baseline commit: 1f65034a92afa4bd10d7cf20e4fd07266387372e
- Baseline lock tag: s43-cp003-a-locked

The CP003-B planning branch currently extends the baseline only through governance documentation.

No executable runtime behavior is changed by this document.

## CP003 Scaffold Boundary

The CP003 scaffold remains isolated under:

- cp003_scaffold/__init__.py
- cp003_scaffold/contracts.py
- cp003_scaffold/safety_law_engine.py
- cp003_scaffold/portfolio_brain.py
- cp003_scaffold/audit_receipt_engine.py

These files may be inspected for planning purposes.

They must not be connected to baseline runtime flow until a later authorized mutation receipt explicitly permits a named integration slice.

## No-Touch Set

The following files and areas are not authorized for modification during this planning stage:

- s43_instrumented_LATEST.py
- 11029.py
- Existing runtime execution paths
- Existing order placement logic
- Existing broker connectivity logic
- Existing live trading switches
- Existing risk gate implementations
- Existing safety boundary checks
- Existing CP003-A receipts, manifests, and lock records
- Any file that imports cp003_scaffold into baseline runtime flow
- Any file that changes trading behavior
- Any file that changes production execution behavior

## Read-Only Inspection Set

The following areas may be inspected, searched, or referenced for planning only:

- Baseline startup flow
- Baseline configuration loading
- Baseline risk gate sequence
- Baseline decision pipeline
- Baseline audit/logging paths
- Baseline portfolio sizing logic, if present
- Baseline safety authorization checks
- Existing CP003 scaffold contracts and neutral modules

Read-only inspection does not authorize edits.

Any finding from inspection must be recorded in a governance document before a mutation proposal is created.

## Allowed Planning Artifacts

The following new files are allowed during CP003-B planning:

- governance/CP003_B_INTEGRATION_INSERTION_MAP.md
- governance/CP003_B_BASELINE_IMPACT_ASSESSMENT.md
- governance/CP003_B_SAFETY_GATE_COMPATIBILITY_REVIEW.md
- governance/CP003_B_ROLLBACK_PLAN.md
- governance/CP003_B_TEST_PLAN.md
- governance/CP003_B_AUTHORIZED_MUTATION_PROPOSAL.md

These artifacts must remain documentation-only unless a later governance decision explicitly changes the allowed scope.

## Candidate Future Integration Slices

The following candidate slices may be studied but are not yet authorized:

### Slice B1: Passive Import Boundary Check

Goal:

- Determine whether cp003_scaffold can be imported in a non-runtime, non-execution context without side effects.

Current authorization:

- Study only.
- No baseline import allowed.

Required before authorization:

- Import side-effect review.
- Static analysis result.
- Rollback plan.
- Explicit mutation receipt.

### Slice B2: Offline Audit Receipt Dry Run

Goal:

- Evaluate AuditReceiptEngine only in an offline test context.

Current authorization:

- Study only.
- No baseline runtime call allowed.

Required before authorization:

- Test-only entrypoint definition.
- No broker access guarantee.
- No live execution guarantee.
- Deterministic output review.

### Slice B3: Safety Law Shadow Evaluation

Goal:

- Evaluate SafetyLawEngine against copied or synthetic inputs without affecting runtime decisions.

Current authorization:

- Study only.
- No runtime decision impact allowed.

Required before authorization:

- Shadow-only architecture.
- Explicit guarantee of no order path modification.
- Test plan.
- Revert path.

### Slice B4: Portfolio Brain Offline Scenario Review

Goal:

- Evaluate PortfolioBrain against offline scenarios.

Current authorization:

- Study only.
- No position sizing change allowed.

Required before authorization:

- Synthetic scenario set.
- No live data dependency.
- No order execution dependency.
- Comparison-only report.

## Disallowed Integration Paths

The following paths are explicitly disallowed at this stage:

- Direct import of cp003_scaffold from s43_instrumented_LATEST.py
- Direct import of cp003_scaffold from 11029.py
- Runtime replacement of existing risk controls
- Runtime replacement of existing portfolio sizing
- Runtime replacement of existing audit logic
- Live trading enablement
- Broker API mutation
- Order placement path mutation
- Safety gate bypass
- Silent fallback to CP003 logic
- Any integration without a rollback plan

## Minimum Requirements Before Mutation Proposal

Before any executable mutation can be proposed, CP003-B must contain:

- Baseline impact assessment
- Safety gate compatibility review
- Rollback plan
- Test plan
- Exact file-level insertion map
- Exact function-level insertion point, if applicable
- Expected behavior statement
- Failure mode statement
- No-live-trading guarantee
- Authorized mutation receipt draft

## Current Ruling

This insertion map is documentation-only.

It does not authorize baseline executable mutation.

It does not authorize runtime integration.

It does not authorize live trading.

The only approved CP003-B work at this point is planning, review, and governance documentation.
