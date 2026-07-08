# Governance Risk Guard Test Plan

## Purpose

This document defines the Phase 12 test plan for the dry-run-first Risk Guard capability.

This is a planning document only.

It does not implement tests.
It does not modify runtime behavior.
It does not modify `s43.py`.
It does not enable enforcement.

## Test Strategy

The Risk Guard must be tested before any runtime integration is considered.

Testing must prove that the component:

- returns a valid structured decision
- supports dry-run mode
- rejects invalid modes and severities
- avoids runtime side effects
- does not import legacy code
- does not mutate wallet or capital state
- can be disabled safely
- can be observed through structured output

## Required Test Categories

### 1. Decision Shape Tests

Goal:

Verify that every Risk Guard evaluation returns the required decision fields.

Required fields:

- `allowed`
- `severity`
- `reason`
- `rule_id`
- `mode`
- `metadata`
- `timestamp`

Expected result:

- all fields exist
- no required field is missing
- unexpected missing values fail validation

### 2. Field Type Tests

Goal:

Verify that each decision field uses the expected type.

Expected types:

- `allowed`: boolean
- `severity`: string
- `reason`: string
- `rule_id`: string
- `mode`: string
- `metadata`: dictionary/object
- `timestamp`: string

Expected result:

- invalid field types are rejected
- valid field types pass

### 3. Severity Validation Tests

Goal:

Verify that only approved severity values are accepted.

Allowed values:

- `info`
- `warning`
- `critical`

Expected result:

- valid severities pass
- unknown severities fail validation

### 4. Mode Validation Tests

Goal:

Verify that only approved modes are accepted.

Allowed values:

- `dry_run`
- `enforce`
- `disabled`

Expected result:

- valid modes pass
- unknown modes fail validation
- default mode is `dry_run`

### 5. Dry-Run No-Side-Effect Tests

Goal:

Prove that dry-run mode never changes runtime behavior.

Dry-run must not:

- block execution
- mutate wallet state
- mutate capital state
- place orders
- cancel orders
- pause the bot
- trigger kill-switch behavior
- change `s43.py` behavior silently

Expected result:

- dry-run only returns advisory decisions
- no state mutation occurs
- no runtime control-flow change occurs

### 6. Missing Context Tests

Goal:

Verify behavior when required risk context is absent or incomplete.

Candidate rule:

- `RG001`: Missing Risk Context

Expected result:

- returns a structured warning decision
- does not raise uncontrolled exceptions
- does not block in dry-run mode

### 7. Abnormal Exposure Tests

Goal:

Verify behavior when exposure-like values exceed expected bounds.

Candidate rule:

- `RG002`: Abnormal Exposure Signal

Expected result:

- returns `allowed = false`
- returns `severity = warning`
- returns `mode = dry_run`
- does not block runtime behavior

### 8. Repeated Failure Tests

Goal:

Verify behavior when repeated runtime or strategy failures are detected.

Candidate rule:

- `RG003`: Repeated Failure Signal

Expected result:

- failure count below threshold returns advisory pass
- failure count above threshold returns warning
- dry-run never blocks behavior

### 9. Critical Drawdown Tests

Goal:

Verify behavior when a severe drawdown-style signal is detected.

Candidate rule:

- `RG004`: Critical Drawdown Signal

Expected result:

- returns `allowed = false`
- returns `severity = critical`
- returns `mode = dry_run`
- does not trigger enforcement in dry-run mode

### 10. Disabled Mode Tests

Goal:

Verify that disabled mode safely bypasses active evaluation.

Expected result:

- disabled mode returns a safe neutral decision or no-op decision
- no rules are enforced
- no runtime mutation occurs

### 11. Metadata Safety Tests

Goal:

Verify that metadata is structured and safe.

Metadata must not contain:

- credentials
- API keys
- secrets
- private tokens
- raw authentication headers

Expected result:

- safe metadata passes
- secret-like metadata fails or is redacted according to final implementation policy

### 12. Legacy Isolation Tests

Goal:

Verify that the future Risk Guard implementation does not depend on legacy runtime code.

Expected result:

- no direct import from `legacy_reference/11029_legacy_reference.py`
- no execution of legacy code
- no direct copy-paste dependency on legacy classes

### 13. Central Hook Boundary Tests

Goal:

Prepare for future runtime integration without approving it yet.

Expected result:

- Risk Guard can be called through a single boundary
- output remains a structured decision
- no scattered calls inside `s43.py`
- hook can ignore dry-run warnings safely

## Proposed Test File Names

Future implementation may use these test files:
```text
tests/test_governance_decision_contract.py
tests/test_risk_guard_dry_run.py
tests/test_risk_guard_validation.py
tests/test_risk_guard_no_side_effects.py
tests/test_risk_guard_rules.py
tests/test_risk_guard_legacy_isolation.py

These file names are proposals only.

## Minimum Acceptance Criteria Before Implementation

Before implementation starts, the project should have:

1. approved decision contract
2. approved dry-run behavior
3. approved rule IDs
4. approved failure behavior
5. approved no-side-effect expectations
6. approved test file layout
7. approved rollback expectations

## Minimum Acceptance Criteria Before Runtime Integration

Before any runtime integration is considered, the project must have:

1. passing unit tests
2. passing dry-run tests
3. passing no-side-effect tests
4. no direct legacy import
5. no scattered `s43.py` injection
6. central hook design reviewed
7. rollback plan documented
8. enforcement disabled by default

## Enforcement Test Policy

Enforcement tests are not part of the current stage.

Current approved test scope:

- contract validation
- dry-run behavior
- no-side-effect guarantees
- disabled behavior
- legacy isolation
- advisory decision output

Not approved yet:

- live blocking tests
- kill-switch activation tests
- runtime mutation tests
- trading behavior modification tests

## Decision

The Risk Guard may proceed to implementation planning only after this test plan is reviewed.

The next safe artifact after this document is:

text
GOVERNANCE_RISK_GUARD_IMPLEMENTATION_PLAN.md

Implementation must remain isolated and must not modify `s43.py` until the central hook design is approved.
