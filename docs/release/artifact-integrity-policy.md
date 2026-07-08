# P2.0 Artifact Integrity Policy

## Purpose

This document defines the artifact integrity baseline for ASO-X releases.

## Integrity Principle

A release artifact must be traceable to repository source, commit identity, checks, and audit evidence.

## Required Artifact Evidence

Release artifact evidence must include:

- source commit
- release version
- build command or generation process
- checks status
- dependency state
- artifact checksum when applicable
- audit evidence location

## Artifact Rules

Artifacts must not be accepted when:

- source commit is unknown
- build process is not reproducible
- dependency state is unknown
- checksum or integrity evidence is missing when required
- artifact was produced outside approved release governance

## Audit Requirement

Artifact integrity must be reviewable after release and after rollback.

## Signature and Provenance Requirements

Release artifacts must provide integrity evidence through checksum and, where applicable, signature validation.
Artifact provenance must identify the source commit, build context, and generation path used for release creation.
