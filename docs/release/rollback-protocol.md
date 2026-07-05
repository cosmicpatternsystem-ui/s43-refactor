# P2.0 Rollback Protocol

## Purpose

This document defines the minimum rollback protocol for ASO-X releases.

## Rollback Principle

Every production release must be reversible before it is approved.

## Required Rollback Data

A rollback plan must identify:

- rollback target
- affected components
- database or state implications
- dependency implications
- artifact replacement procedure
- verification procedure after rollback

## Rollback Triggers

Rollback must be considered when:

- release health checks fail
- production readiness assumptions are invalid
- incident severity exceeds tolerance
- artifact integrity cannot be verified
- critical dependency behavior changes unexpectedly

## Rollback Completion Evidence

Rollback is complete only when:

- target version is restored
- health checks pass
- incident notes are recorded
- audit evidence is preserved
- follow-up remediation is tracked
