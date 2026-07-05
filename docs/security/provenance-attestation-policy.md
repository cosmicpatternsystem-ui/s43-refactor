# P2.8 Provenance Attestation Baseline

## Purpose

Define a deterministic, repository-local, network-free provenance attestation artifact for ASO-X governance artifacts and release hardening evidence.

## Scope

This policy applies to provenance attestations stored in the repository as audit artifacts. The baseline is intended to prove that an artifact was generated from a specific repository state and validated under policy-controlled conditions.

## Required Artifact Fields

A provenance attestation artifact MUST be a JSON object containing:

- `schema_version`
- `attestation_id`
- `generated_at_utc`
- `source_repository`
- `branch`
- `commit`
- `subject`
- `build_definition`
- `predicate`
- `release_evidence_bundle_path`
- `supply_chain_integrity_path`
- `sbom_path`
- `network_free_validation`
- `mutable_external_sources_allowed`
- `policy_audit_passed`
- `validation_evidence`

## Rules

### 1. Schema Version

- `schema_version` MUST begin with `aso-x.provenance_attestation.`

### 2. Identity and Source

- `attestation_id` MUST be a non-empty string.
- `generated_at_utc` MUST be an ISO-8601 UTC timestamp ending with `Z`.
- `source_repository` MUST be a non-empty string naming the repository.
- `branch` MUST be a non-empty string.
- `commit` MUST be a lowercase 40-character hexadecimal git commit SHA-1.

### 3. Subject

- `subject` MUST be a JSON object.
- `subject.name` MUST be a non-empty string.
- `subject.type` MUST be a non-empty string.
- `subject.path` MUST be a repository-relative safe path.
- `subject.digest_sha256` MUST be a lowercase 64-character hexadecimal SHA-256 digest.

### 4. Build Definition

- `build_definition` MUST be a JSON object.
- It MUST contain:
  - `build_type`
  - `builder`
  - `invocation`
- `build_definition.build_type` MUST be a non-empty string.
- `build_definition.builder` MUST be a JSON object with:
  - `id`
  - `version`
- `build_definition.invocation` MUST be a JSON object with:
  - `config_source`
  - `parameters`
  - `environment`

### 5. Predicate

- `predicate` MUST be a JSON object.
- It MUST contain:
  - `materials`
  - `metadata`
- `predicate.materials` MUST be a non-empty list.
- Each material MUST contain:
  - `name`
  - `uri`
  - `digest`
- `digest` for each material MUST be a JSON object containing at least one non-empty digest entry.
- `predicate.metadata` MUST contain:
  - `completeness`
  - `reproducible`
  - `build_finished_on_utc`
- `predicate.metadata.build_finished_on_utc` MUST be an ISO-8601 UTC timestamp ending with `Z`.

### 6. Cross-Baseline Links

The following fields MUST be repository-relative safe paths:

- `release_evidence_bundle_path`
- `supply_chain_integrity_path`
- `sbom_path`

These fields bind the attestation to:
- P2.5 Release Evidence Bundle Baseline
- P2.6 Supply Chain Integrity Baseline
- P2.7 SBOM Baseline

### 7. Repository Safety

All artifact paths in this document MUST:
- be relative to the repository root
- NOT be absolute
- NOT contain parent traversal such as `..`
- use repository-local auditable locations only

### 8. Validation and Mutability Constraints

- `network_free_validation` MUST be `true`
- `mutable_external_sources_allowed` MUST be `false`
- `policy_audit_passed` MUST be `true`

### 9. Validation Evidence

- `validation_evidence` MUST be a JSON object containing:
  - `validator_command`
  - `test_command`
  - `validator_exit_code`
  - `test_exit_code`

- `validator_command` and `test_command` MUST be non-empty strings.
- `validator_exit_code` MUST equal `0`.
- `test_exit_code` MUST equal `0`.

## Compliance Outcome

An attestation is compliant only if all required fields are present, all repository paths are safe, all linked baseline artifacts are referenced, and validation evidence proves successful deterministic verification.

## Notes

This baseline is intentionally repository-local and minimal. It provides durable provenance evidence without relying on online services, mutable remote registries, or external attestation infrastructure.