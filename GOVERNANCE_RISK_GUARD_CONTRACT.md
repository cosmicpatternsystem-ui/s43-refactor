# Governance Risk Guard Contract

## Purpose

This document defines the Phase 12 contract for a dry-run-first Risk Guard capability.

The Risk Guard is intended to evaluate risk conditions and return structured governance decisions without directly changing runtime behavior.

This is a design contract only.

It does not implement runtime logic.
It does not modify `s43.py`.
It does not enable enforcement.
It does not approve direct migration from legacy code.

## Scope

The Risk Guard may evaluate risk signals and produce advisory decisions.

Examples of possible future inputs:

- account state
- wallet state
- exposure state
- volatility signals
- drawdown indicators
- repeated failure signals
- abnormal movement signals
- timing-related risk signals
- strategy-level risk metadata

These inputs are conceptual and must be formalized before implementation.

## Non-Goals

The Risk Guard must not:

- mutate wallet state
- mutate capital state
- place orders
- cancel orders
- stop runtime execution directly
- import legacy code directly
- inject checks into scattered locations inside `s43.py`
- silently change trading behavior
- enforce decisions before explicit activation gates pass

## Required Decision Object

Every Risk Guard evaluation must return a structured decision object.

Required fields:
```text
allowed
severity
reason
rule_id
mode
metadata
timestamp

## Field Definitions

### allowed

Type: boolean

Meaning:

- `true`: the evaluated condition does not recommend blocking action
- `false`: the evaluated condition recommends blocking or pausing action

In dry-run mode, `allowed = false` must not block runtime behavior.

### severity

Type: string

Allowed values:

text
info
warning
critical

Meaning:

- `info`: normal advisory signal
- `warning`: risk condition observed, no enforcement
- `critical`: high-risk condition observed, enforcement may be considered only if enabled and approved

### reason

Type: string

A human-readable explanation of the decision.

Requirements:

- clear
- short
- non-empty
- suitable for logs and reports

### rule_id

Type: string

A stable identifier for the rule that produced the decision.

Example format:

text
RG001
RG002
RG003

Rule IDs must be stable once introduced.

### mode

Type: string

Allowed values:

text
dry_run
enforce
disabled

Meaning:

- `dry_run`: evaluate and report only
- `enforce`: evaluate and allow enforcement behavior if all activation gates pass
- `disabled`: do not evaluate active risk rules

Phase 12 default mode must be:

text
dry_run

### metadata

Type: object / dictionary

Optional structured context.

Examples:

text
signal_name
observed_value
threshold
source
symbol
timeframe
wallet_id
cycle_id

Metadata must not contain secrets or credentials.

### timestamp

Type: string

Recommended format:

text
ISO-8601 UTC

Example:

text
2026-06-12T12:30:00Z

## Dry-Run Requirements

Dry-run mode is mandatory before enforcement.

In dry-run mode, the Risk Guard may:

- evaluate risk signals
- produce structured decisions
- log advisory results
- emit warnings
- collect metrics
- support test assertions

In dry-run mode, the Risk Guard must not:

- block execution
- alter runtime control flow
- alter wallet state
- alter capital state
- place or cancel orders
- pause the bot
- trigger kill-switch behavior
- modify `s43.py` behavior silently

## Enforcement Requirements

Enforcement is not approved in the current stage.

Future enforcement may be considered only after:

1. contract tests exist
2. dry-run tests exist
3. no-side-effect tests exist
4. rollback behavior is documented
5. central runtime hook is designed
6. configuration gates are defined
7. observability is implemented
8. explicit approval is recorded

## Suggested Initial Rules

These rule ideas are candidates only.

### RG001: Missing Risk Context

Purpose:

Detect when required risk context is missing.

Default severity:

text
warning

Default dry-run behavior:

Return advisory decision only.

### RG002: Abnormal Exposure Signal

Purpose:

Detect exposure values outside expected bounds.

Default severity:

text
warning

Default dry-run behavior:

Return advisory decision only.

### RG003: Repeated Failure Signal

Purpose:

Detect repeated failed runtime or strategy events.

Default severity:

text
warning

Default dry-run behavior:

Return advisory decision only.

### RG004: Critical Drawdown Signal

Purpose:

Detect severe drawdown-style risk condition.

Default severity:

text
critical

Default dry-run behavior:

Return advisory decision only.

No blocking is allowed in dry-run mode.

## Interface Sketch

Future implementation may expose a function or class with this conceptual shape:

text
evaluate_risk(context, mode="dry_run") -> GovernanceDecision

This is not implementation approval.

The final interface must be reviewed before code is added.

## Expected Behavior Examples

### Example 1: Normal Advisory Pass

text
allowed: true
severity: info
reason: No risk condition detected
rule_id: RG000
mode: dry_run
metadata: {}
timestamp: 2026-06-12T12:30:00Z

### Example 2: Dry-Run Warning

text
allowed: false
severity: warning
reason: Repeated failure signal detected
rule_id: RG003
mode: dry_run
metadata:
  failure_count: 3
  threshold: 2
timestamp: 2026-06-12T12:31:00Z

Important:

Even when `allowed` is false, dry-run mode must not block runtime behavior.

### Example 3: Critical Dry-Run Signal

text
allowed: false
severity: critical
reason: Critical drawdown signal detected
rule_id: RG004
mode: dry_run
metadata:
  observed_drawdown: 0.18
  threshold: 0.15
timestamp: 2026-06-12T12:32:00Z

Important:

Critical dry-run signals are advisory only.

## Testing Requirements

Before implementation, the following tests must be planned:

- decision object shape test
- allowed field type test
- severity allowed-values test
- mode allowed-values test
- metadata no-secret test
- dry-run no-side-effect test
- missing context test
- repeated failure rule test
- critical signal rule test

## Rollback Requirements

Any future Risk Guard implementation must be removable or disableable without affecting runtime stability.

Minimum rollback requirements:

- mode can be set to `disabled`
- dry-run can remain available without enforcement
- central hook can ignore Risk Guard output
- no scattered calls inside `s43.py`
- no dependency on legacy code at runtime

## Approval Status

Current status:

text
contract-draft

Approved for:

text
documentation
design review
test planning

Not approved for:

text
runtime enforcement
direct integration
legacy code migration
s43.py modification

## Decision

Phase 12 may proceed from capability inventory to Risk Guard contract review.

The next safe step after this document is to create a test plan document before implementation.
