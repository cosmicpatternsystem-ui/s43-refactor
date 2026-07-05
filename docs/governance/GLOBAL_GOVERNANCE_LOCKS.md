# Global Governance Lock System

This document defines the repository-wide global governance lock system for enterprise-grade 50-year durability.

## Source of Truth

The repository is the source of truth.

## Machine Registry
`	ext
docs/governance/global-governance-locks.json

## Schema

text
docs/governance/global-governance-locks.schema.json

## Test Gate

text
tests/test_global_governance_locks.py

## CI Gate

text
.github/workflows/global-governance-locks-gate.yml

## Mandatory Rules

1. Every lock must have an immutable GOV-LOCK-XXX identifier.
2. Every lock must exist in the JSON registry.
3. Every lock must be represented in this Markdown index.
4. Every lock must be covered by pytest validation.
5. Every lock must be covered by GitHub Actions validation.
6. Every lock must use 50y retention.
7. Every lock must use lock merge failure mode.
8. Every lock must use deletion_allowed = false.
9. Critical and high-risk locks must require evidence.
10. Supersession is allowed only through documented PR review.

## Lock Matrix

| ID | Name | Risk | Scope | Retention | Failure Mode |
|---|---|---|---|---|---|
| GOV-LOCK-001 | Immutable Roadmap ID Registry | critical | repository-wide | 50y | block merge |
| GOV-LOCK-002 | Immutable Requirement ID Registry | critical | repository-wide | 50y | block merge |
| GOV-LOCK-003 | Immutable Governance Lock ID Registry | critical | repository-wide | 50y | block merge |
| GOV-LOCK-004 | Source-of-Truth Repository Lock | critical | repository-wide | 50y | block merge |
| GOV-LOCK-005 | Governance Change Approval Matrix | critical | repository-wide | 50y | block merge |
| GOV-LOCK-006 | Deprecation and Supersession Lock | high | repository-wide | 50y | block merge |
| GOV-LOCK-007 | Artifact Retention 50-Year Lock | critical | repository-wide | 50y | block merge |
| GOV-LOCK-008 | Evidence Ledger Lock | critical | repository-wide | 50y | block merge |
| GOV-LOCK-009 | Release Evidence Lock | high | release-wide | 50y | block merge |
| GOV-LOCK-010 | Baseline Drift Detection Lock | critical | repository-wide | 50y | block merge |
| GOV-LOCK-011 | AI Handoff Completeness Lock | high | repository-wide | 50y | block merge |
| GOV-LOCK-012 | CI Schema Validation Lock | critical | ci-wide | 50y | block merge |
| GOV-LOCK-013 | Branch and PR Merge Policy Lock | critical | repository-wide | 50y | block merge |
| GOV-LOCK-014 | Required Review Lock | high | repository-wide | 50y | block merge |
| GOV-LOCK-015 | Test Coverage Gate Lock | high | repository-wide | 50y | block merge |
| GOV-LOCK-016 | Security Review Trigger Lock | critical | repository-wide | 50y | block merge |
| GOV-LOCK-017 | Dependency and Supply Chain Lock | critical | repository-wide | 50y | block merge |
| GOV-LOCK-018 | Financial-Risk Change Control Lock | critical | repository-wide | 50y | block merge |
| GOV-LOCK-019 | Disaster Recovery Lock | critical | repository-wide | 50y | block merge |
| GOV-LOCK-020 | Repository Portability Lock | high | repository-wide | 50y | block merge |
| GOV-LOCK-021 | Encoding UTF-8 LF Lock | high | repository-wide | 50y | block merge |
| GOV-LOCK-022 | cp1252-Safe Output Lock | medium | tooling-wide | 50y | block merge |
| GOV-LOCK-023 | Atomic Write Lock | high | tooling-wide | 50y | block merge |
| GOV-LOCK-024 | Concurrent Edit Safety Lock | high | repository-wide | 50y | block merge |
| GOV-LOCK-025 | Immutable Git History Policy Lock | critical | repository-wide | 50y | block merge |
| GOV-LOCK-026 | Machine-Readable Index Lock | high | repository-wide | 50y | block merge |
| GOV-LOCK-027 | Documentation Completeness Lock | high | repository-wide | 50y | block merge |
| GOV-LOCK-028 | Ownership and Stewardship Lock | critical | repository-wide | 50y | block merge |
| GOV-LOCK-029 | External Interface Stability Lock | high | interface-wide | 50y | block merge |
| GOV-LOCK-030 | Backward Compatibility Review Lock | high | repository-wide | 50y | block merge |
| GOV-LOCK-031 | Operational Runbook Lock | high | operations-wide | 50y | block merge |
| GOV-LOCK-032 | Long-Term Maintenance and Succession Lock | critical | repository-wide | 50y | block merge |

## Change Control

text
PR + required review + CI pass

## Retention

text
50y