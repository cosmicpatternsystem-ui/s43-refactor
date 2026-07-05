# P2.0 Release Governance

## Purpose

This document defines the release governance baseline for ASO-X.

A release is not valid unless it is traceable, auditable, reversible, and produced from the repository source of truth.

## Source Of Truth

- `main` is the only production source of truth.
- Direct push to `main` is not an approved release path.
- Release changes must enter through pull requests.
- Release merges must pass checks, policy gates, and safe merge audit evidence.

## Required Release Evidence

Every release candidate must provide:

- release scope
- version decision
- dependency status
- production readiness status
- rollback plan
- artifact integrity evidence
- audit evidence

## Release Approval Rule

A release must not be approved if any of the following are missing:

- green checks
- clean worktree
- rollback protocol
- incident response owner
- dependency freeze decision
- artifact integrity verification
- safe merge audit trail

## Relationship To Existing Documents

This P2.0 baseline complements existing release process and release runbook documents.
