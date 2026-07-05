# P2.0 Incident Response Protocol

## Purpose

This document defines the release incident response baseline for ASO-X.

## Incident Principle

An incident must be handled through clear ownership, preserved evidence, and controlled remediation.

## Required Incident Fields

Every release incident must record:

- detection time
- affected release version
- severity
- owner
- customer or operational impact
- mitigation action
- rollback decision
- audit evidence location

## Incident Severity

Minimum severity classes:

- sev1: production unavailable or financial integrity risk
- sev2: degraded production behavior or major operational risk
- sev3: limited impact with known workaround
- sev4: informational or near-miss event

## Response Requirements

For release-impacting incidents:

- stop further release promotion
- preserve logs and audit evidence
- assign owner
- decide rollback or forward fix
- record final resolution
