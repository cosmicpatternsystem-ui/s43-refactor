# Governance Risk Guard Implementation Plan

## Purpose

This document defines the implementation plan for the Phase 12 Risk Guard capability.

This is a planning document only.

It does not implement code.
It does not modify `s43.py`.
It does not activate enforcement.
It does not import legacy code.
It does not approve runtime integration.

## Current Status

Phase 12 has completed the following design artifacts:

- `PHASE12_GOVERNANCE_DESIGN.md`
- `GOVERNANCE_CAPABILITY_INVENTORY.md`
- `GOVERNANCE_RISK_GUARD_CONTRACT.md`
- `GOVERNANCE_RISK_GUARD_TEST_PLAN.md`

The next step is to define a safe implementation path.

## Implementation Principles

The implementation must follow these principles:

- isolated module first
- tests before runtime integration
- dry-run default
- no direct enforcement
- no direct modification to `s43.py`
- no direct import from legacy reference files
- no scattered runtime checks
- no hidden side effects
- structured decisions only
- explicit rollback path

## Approved Initial Scope

The first implementation stage may include:

- a governance decision data structure
- validation for decision fields
- severity validation
- mode validation
- dry-run behavior
- disabled-mode behavior
- a minimal Risk Guard evaluator
- unit tests for the contract
- unit tests for dry-run no-side-effect behavior

The first implementation stage must not include:

- runtime hook activation
- enforcement behavior
- kill-switch behavior
- wallet mutation
- capital mutation
- order placement
- order cancellation
- direct `s43.py` edits
- legacy code execution

## Proposed File Layout

Future implementation may use this structure:
```text
governance/
  __init__.py
  decisions.py
  risk_guard.py

tests/
  test_governance_decision_contract.py
  test_risk_guard_dry_run.py
  test_risk_guard_validation.py
  test_risk_guard_no_side_effects.py
  test_risk_guard_legacy_isolation.py

This layout is proposed for isolated implementation only.

## Proposed Module Responsibilities

### governance/decisions.py

Purpose:

Define the governance decision object and validation helpers.

Possible responsibilities:

- define required fields
- validate `allowed`
- validate `severity`
- validate `reason`
- validate `rule_id`
- validate `mode`
- validate `metadata`
- validate `timestamp`

Non-responsibilities:

- no runtime mutation
- no trading logic
- no wallet logic
- no capital logic
- no legacy import

### governance/risk_guard.py

Purpose:

Evaluate risk context and return structured governance decisions.

Possible responsibilities:

- evaluate missing context
- evaluate abnormal exposure signals
- evaluate repeated failure signals
- evaluate critical drawdown signals
- return advisory decisions in dry-run mode
- return neutral decisions in disabled mode

Non-responsibilities:

- no blocking in dry-run mode
- no direct enforcement
- no runtime shutdown
- no wallet mutation
- no capital mutation
- no order mutation
- no direct `s43.py` coupling

## Proposed Decision Object

The implementation should follow the contract from `GOVERNANCE_RISK_GUARD_CONTRACT.md`.

Required fields:

text
allowed
severity
reason
rule_id
mode
metadata
timestamp

Default safe decision:

text
allowed: true
severity: info
reason: No risk condition detected
rule_id: RG000
mode: dry_run
metadata: {}
timestamp: ISO-8601 UTC

## Proposed Initial Rules

### RG000: No Risk Condition

Purpose:

Return a safe advisory pass when no risk condition is detected.

Expected dry-run result:

text
allowed: true
severity: info
reason: No risk condition detected
rule_id: RG000
mode: dry_run
metadata: {}

### RG001: Missing Risk Context

Purpose:

Detect missing or incomplete risk context.

Expected dry-run result:

text
allowed: false
severity: warning
reason: Missing risk context
rule_id: RG001
mode: dry_run

### RG002: Abnormal Exposure Signal

Purpose:

Detect exposure values outside expected bounds.

Expected dry-run result:

text
allowed: false
severity: warning
reason: Abnormal exposure signal detected
rule_id: RG002
mode: dry_run

### RG003: Repeated Failure Signal

Purpose:

Detect repeated failed events above a configured threshold.

Expected dry-run result:

text
allowed: false
severity: warning
reason: Repeated failure signal detected
rule_id: RG003
mode: dry_run

### RG004: Critical Drawdown Signal

Purpose:

Detect severe drawdown-style risk condition.

Expected dry-run result:

text
allowed: false
severity: critical
reason: Critical drawdown signal detected
rule_id: RG004
mode: dry_run

## Implementation Sequence

Implementation must proceed in small, reviewable steps.

### Step 1: Create Isolated Governance Package

Create:

text
governance/__init__.py
governance/decisions.py
governance/risk_guard.py

Constraints:

- no `s43.py` changes
- no runtime hook
- no legacy import
- no enforcement

### Step 2: Add Decision Contract Tests

Create tests for:

- required fields
- field types
- allowed severities
- allowed modes
- default dry-run mode
- metadata structure
- timestamp presence

### Step 3: Implement Decision Validation

Implement enough code to pass contract tests.

Constraints:

- pure validation only
- no runtime mutation
- no side effects

### Step 4: Add Risk Guard Dry-Run Tests

Create tests for:

- RG000 normal pass
- RG001 missing context
- RG002 abnormal exposure
- RG003 repeated failure
- RG004 critical drawdown
- disabled mode
- dry-run no-side-effect behavior

### Step 5: Implement Minimal Risk Guard

Implement only dry-run and disabled behavior.

Constraints:

- enforcement mode may be recognized but must not perform live blocking
- dry-run must only return advisory decisions
- disabled mode must safely no-op

### Step 6: Add Legacy Isolation Tests

Create tests proving:

- no direct import from `legacy_reference/11029_legacy_reference.py`
- no dependency on legacy runtime classes
- no legacy file execution

### Step 7: Review Before Runtime Boundary Design

Stop after isolated tests pass.

Do not modify `s43.py`.

The next separate artifact must be central hook design, not direct runtime integration.

## Dry-Run Behavior

Dry-run must be the default.

Dry-run may:

- evaluate context
- return advisory decisions
- expose structured metadata
- support logs or reports in future stages

Dry-run must not:

- block execution
- mutate state
- place orders
- cancel orders
- pause runtime
- trigger kill-switch behavior
- change `s43.py`

## Disabled Behavior

Disabled mode must be safe.

Allowed disabled behavior:

- return neutral no-op decision
- skip rule evaluation
- expose mode as `disabled`

Disabled mode must not:

- emit warnings as enforcement
- mutate runtime state
- hide side effects
- call legacy code

## Enforcement Policy

Enforcement is not approved in this implementation plan.

If `mode = enforce` is introduced in code, it must remain inert unless a later approved document explicitly defines enforcement behavior.

Current allowed behavior for enforce mode:

- validate the mode
- return structured decisions
- avoid live blocking
- avoid runtime mutation

## Testing Commands

Future implementation should be verified with available project test tooling.

Potential commands:

text
python -m pytest tests/test_governance_decision_contract.py
python -m pytest tests/test_risk_guard_dry_run.py
python -m pytest tests/test_risk_guard_validation.py
python -m pytest tests/test_risk_guard_no_side_effects.py
python -m pytest tests/test_risk_guard_legacy_isolation.py
python -m pytest
python -m py_compile s43.py

Actual commands may be adjusted to match the repository test setup.

## Rollback Plan

Rollback must remain simple.

If implementation causes issues:

- remove the isolated `governance/` package
- remove related tests
- keep documentation commits as design history if desired
- do not touch Phase 11 checkpoint tags
- do not alter `s43.py`

Because runtime integration is not part of this plan, rollback should not affect production runtime behavior.

## Completion Criteria

This implementation planning stage is complete when:

- isolated file layout is approved
- initial rule list is approved
- dry-run-only behavior is approved
- disabled behavior is approved
- test sequence is approved
- enforcement remains explicitly out of scope
- `s43.py` remains unchanged

## Next Safe Step

After this document is committed, the next safe step is one of:

1. create isolated tests first
2. create governance package skeleton with no runtime integration
3. create central hook design document before any runtime work

Recommended next step:

text
create isolated tests first

## Decision

Phase 12 may proceed from test planning to isolated implementation planning.

Runtime integration remains blocked until a separate central hook design is approved.
