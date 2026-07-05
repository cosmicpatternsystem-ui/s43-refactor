# P2.0 Versioning Policy

## Purpose

This document defines the versioning policy for ASO-X releases.

## Version Rule

ASO-X releases must use explicit, reviewable version identifiers.

A version must communicate:

- release identity
- compatibility expectation
- rollback target
- audit traceability

## Version Classes

Allowed version classes:

- major: incompatible operational or contract change
- minor: compatible capability addition
- patch: compatible fix, hardening, or documentation correction
- prerelease: non-production validation candidate

## Version Decision Requirements

Before release approval, the release owner must document:

- selected version
- previous version
- reason for version increment
- rollback version
- compatibility notes

## Prohibited Version Practices

The following are not allowed:

- implicit production release without version decision
- untracked binary or artifact version
- release from a non-main branch
- release without audit evidence

## Semantic Versioning and Tag Policy

All release identifiers must follow semantic versioning principles.
Each approved release must be published with a corresponding Git tag.
The release tag must map unambiguously to the audited release commit.
