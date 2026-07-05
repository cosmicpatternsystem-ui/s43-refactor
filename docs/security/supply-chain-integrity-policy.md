# Supply Chain Integrity Policy

## Purpose

This document defines the baseline supply chain integrity policy for ASO-X.

The goal is to ensure that repository-controlled release work can be reviewed against
a deterministic baseline for source identity, dependency tracking, mutable-source
restriction, and release evidence linkage.

## Scope

This baseline applies to repository-contained supply chain integrity artifacts.

This phase defines:
- the required supply chain integrity artifact structure,
- the minimum required source and dependency evidence fields,
- deterministic validation rules,
- and repository-safe validation expectations.

This phase does not define:
- full SBOM generation,
- cryptographic signing,
- external package registry verification,
- provenance attestation,
- reproducible build enforcement,
- or third-party supply chain scanning.

## Required Artifact Fields

A valid supply chain integrity artifact must contain:

- `schema_version`
- `artifact_id`
- `generated_at_utc`
- `source_repository`
- `branch`
- `commit`
- `policy_document_path`
- `release_evidence_bundle_path`
- `tracked_dependency_files`
- `dependency_lockfiles_present`
- `network_free_validation`
- `mutable_external_sources_allowed`
- `validation_evidence`
- `policy_audit_passed`

## Field Rules

### schema_version

Must be a non-empty string beginning with:

`aso-x.supply_chain_integrity.`

### artifact_id

Must be a non-empty string.

### generated_at_utc

Must be a non-empty UTC timestamp string in ISO-8601 `Z` form.

### source_repository

Must be a non-empty string identifying the source repository.

### branch

Must be a non-empty string.

### commit

Must be a 40-character lowercase hexadecimal Git commit id.

### policy_document_path

Must be a non-empty repository-relative path string.

### release_evidence_bundle_path

Must be a non-empty repository-relative path string.

### tracked_dependency_files

Must be a non-empty list of repository-relative path strings.

### dependency_lockfiles_present

Must be a boolean.

For this baseline, it must be `true`.

### network_free_validation

Must be a boolean.

For this baseline, it must be `true`.

### mutable_external_sources_allowed

Must be a boolean.

For this baseline, it must be `false`.

### validation_evidence

Must be a non-empty object containing:

- `validator_command`
- `test_command`
- `validator_exit_code`
- `test_exit_code`

`validator_command` and `test_command` must be non-empty strings.

`validator_exit_code` and `test_exit_code` must be integers equal to `0`.

### policy_audit_passed

Must be a boolean.

For this baseline, it must be `true`.

## Repository Safety

All governed files introduced by this baseline must be:
- UTF-8 without BOM,
- LF line endings,
- stored inside the repository,
- and reviewable through PR workflows.

## Determinism

Validation must not require:
- network access,
- external services,
- package registry calls,
- mutable external state,
- or environment-specific secrets.

## Relationship to Release Evidence Bundle

The supply chain integrity artifact complements the release evidence bundle.

The release evidence bundle records release review evidence.
The supply chain integrity artifact records source and dependency integrity evidence.

A release may reference both artifacts during governance review.

## Operational Rule

A supply chain integrity artifact may be used as baseline evidence only when:
- the artifact passes validator checks,
- tracked dependency files are explicitly listed,
- mutable external sources are disallowed,
- validation is network-free,
- and `policy_audit_passed` is `true`.