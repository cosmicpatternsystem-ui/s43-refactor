# P2.0 Dependency Freeze Policy

## Purpose

This document defines the dependency freeze policy for ASO-X release candidates.

## Freeze Principle

Dependency changes must be intentional, reviewed, and auditable.

## Tracked Dependency Files

The release process must account for tracked dependency files, including:

- `requirements.txt`
- `requirements-dev.txt`
- `dashboard/package.json`
- `dashboard/package-lock.json`

## Freeze Requirements

Before release approval:

- dependency changes must be reviewed
- lockfile changes must be intentional
- dependency risk must be documented
- security-sensitive changes must be identified
- rollback impact must be understood

## Prohibited Dependency Practices

The following are not allowed:

- unreviewed dependency upgrade during release
- lockfile drift without explanation
- dependency change without rollback consideration
- production release with unknown dependency state
