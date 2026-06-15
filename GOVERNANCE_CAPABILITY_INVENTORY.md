# Governance Capability Inventory

## Purpose

This document inventories governance-related capabilities observed in `legacy_reference/11029_legacy_reference.py`.

It is a design input only.

This file does not approve any capability for runtime use.
This file does not authorize direct migration into `s43.py`.
This file does not override Phase 12 safety rules.

## Inventory Rules

- Legacy code is reference-only.
- Raw legacy implementation must not be copied directly into production runtime.
- Every capability must be redesigned behind a clean contract.
- Every capability must support dry-run before any enforcement path is considered.
- No capability may be injected directly into `s43.py`.

## Capability Status Legend

- `candidate`: potentially useful, not approved
- `defer`: known idea, postpone evaluation
- `reject`: not suitable for migration in current form
- `review-first`: requires architectural review before any design work

## Candidate Inventory

### 1. Capital Protection

- Capability: capital protection / capital kill-switch style logic
- Legacy status: present as a concept in legacy codebase
- Migration status: `review-first`
- Reason: high impact, high blast radius, requires strict dry-run and rollback design
- Notes: must never be migrated by direct injection

### 2. Timing Guard / Runtime Gate

- Capability: timing-based gating for new actions
- Legacy status: present as a concept in legacy codebase
- Migration status: `review-first`
- Reason: central gating logic is sensitive and must be redesigned as a contract-based hook
- Notes: candidate for future central runtime hook design, not direct reuse

### 3. Risk Guard / Risk Sentinel

- Capability: risk evaluation and decision signaling
- Legacy status: present in multiple forms in legacy logic
- Migration status: `candidate`
- Reason: useful as a dry-run decision engine if isolated from runtime mutation
- Notes: should return structured decisions, not directly block behavior

### 4. Equity Shock Detection

- Capability: shock detection / abnormal movement detection
- Legacy status: present as a guard concept
- Migration status: `candidate`
- Reason: can be modeled as an observable signal producer before any enforcement path
- Notes: suitable for dry-run-first evaluation

### 5. Wallet Cycle Guard

- Capability: wallet-cycle or repetition-control logic
- Legacy status: historically explored in earlier work
- Migration status: `candidate`
- Reason: likely lower-risk than kill-switch class protections if reduced to advisory mode
- Notes: good candidate for contract-first design

### 6. Cooldown / Pause Behavior

- Capability: temporary pause or cooldown after defined risk conditions
- Legacy status: conceptually present across governance-style legacy patterns
- Migration status: `candidate`
- Reason: may be expressible in dry-run mode with clear observability
- Notes: should remain advisory until test coverage exists

### 7. Emergency Pause / Hard Stop

- Capability: emergency stop behavior
- Legacy status: implied by kill-switch style controls
- Migration status: `defer`
- Reason: too sensitive for early Phase 12 extraction
- Notes: revisit only after decision contracts and central hook architecture are stable

## Prioritization

Recommended evaluation order:

1. Risk Guard / Risk Sentinel
2. Wallet Cycle Guard
3. Equity Shock Detection
4. Cooldown / Pause Behavior
5. Timing Guard / Runtime Gate
6. Capital Protection
7. Emergency Pause / Hard Stop

## Recommended First Extraction Candidate

Recommended first candidate: `Risk Guard / Risk Sentinel`

Why this is the best first step:

- easier to model as a decision contract
- compatible with dry-run-first policy
- lower risk than capital or hard-stop enforcement
- easier to test without mutating runtime behavior
- suitable for structured observability

## Required Next Artifact

The next design artifact should define a contract for the first selected capability.

Recommended next document:

- `GOVERNANCE_RISK_GUARD_CONTRACT.md`

## Explicit Non-Goals

This inventory does not:

- change runtime behavior
- modify `s43.py`
- enable enforcement
- approve direct legacy migration
- authorize hidden hooks or scattered checks

## Decision

Phase 12 should proceed with contract design for a dry-run-first risk decision component before any runtime integration is considered.
