# Release Evidence Bundle Policy

## Purpose

This document defines the baseline policy for a release evidence bundle in ASO-X.
The release evidence bundle is a repository-contained artifact that groups the minimum
evidence required to review a release decision consistently and deterministically.

## Scope

This baseline applies to repository-stored release evidence bundle artifacts used for
governance review, audit preparation, and release validation.

This phase defines:
- the required bundle structure,
- the minimum required evidence references,
- the baseline validation rules,
- and deterministic repository-safe expectations.

This phase does not define:
- cryptographic signing,
- external artifact retrieval,
- CI enforcement expansion,
- production deployment approval workflows,
- or third-party evidence verification.

## Required Bundle Fields

A valid release evidence bundle artifact must contain the following required keys:

- `schema_version`
- `bundle_id`
- `release_id`
- `branch`
- `commit`
- `generated_at_utc`
- `policy_document_path`
- `attestation_path`
- `audit_artifact_path`
- `test_evidence`
- `policy_audit_passed`

## Field Rules

### schema_version
Must be a non-empty string beginning with:

`aso-x.release_evidence_bundle.`

### bundle_id
Must be a non-empty string.

### release_id
Must be a non-empty string.

### branch
Must be a non-empty string.

### commit
Must be a 40-character lowercase hexadecimal Git commit id.

### generated_at_utc
Must be a non-empty UTC timestamp string in ISO-8601 `Z` form.

### policy_document_path
Must be a non-empty repository-relative path string.

### attestation_path
Must be a non-empty repository-relative path string.

### audit_artifact_path
Must be a non-empty repository-relative path string.

### test_evidence
Must be a non-empty object containing:
- `validator_command`
- `test_command`
- `validator_exit_code`
- `test_exit_code`

`validator_command` and `test_command` must be non-empty strings.  
`validator_exit_code` and `test_exit_code` must be integers equal to `0`.

### policy_audit_passed
Must be a boolean.

## Repository Safety

All governed files introduced by this baseline must be:
- UTF-8 without BOM,
- LF line endings,
- stored inside the repository,
- and reviewable through standard PR workflows.

## Determinism

Validation must be deterministic and must not require:
- network access,
- external services,
- external mutable state,
- or environment-specific secret material.

## Relationship to Prior Governance Artifacts

A release evidence bundle complements:
- release governance policy,
- release audit trail artifacts,
- and release attestation artifacts.

It does not replace them.
It binds them into a single review-oriented evidence structure.

## Operational Rule

A release evidence bundle may be used as a baseline evidence artifact only when:
- the artifact passes validator checks,
- required evidence references are present and non-empty,
- and `policy_audit_passed` is `true`.