# P2.9 Artifact Retention / Evidence Retention Baseline

## Purpose
Define a deterministic, repository-local, policy-auditable baseline for retention of audit,
security, release, and provenance evidence artifacts so that ASO-X remains durable, reproducible,
reviewable, and operationally resilient over long time horizons.

## Scope
This baseline governs repository-local retention declarations for policy evidence artifacts,
including but not limited to:

- release evidence bundles
- supply chain integrity artifacts
- SBOM artifacts
- provenance attestation artifacts
- policy validation evidence
- supporting governance metadata

## Required artifact
The repository MUST contain a repository-local JSON artifact at:

`docs/security/audit/sample-artifact-retention.json`

## Required top-level fields
The artifact MUST contain:

- `schema_version`
- `retention_policy_id`
- `generated_at_utc`
- `source_repository`
- `branch`
- `commit`
- `retention_class`
- `default_retention`
- `artifacts`
- `review`
- `release_evidence_bundle_path`
- `supply_chain_integrity_path`
- `sbom_path`
- `provenance_attestation_path`
- `network_free_validation`
- `mutable_external_sources_allowed`
- `policy_audit_passed`
- `validation_evidence`

## Schema and identity rules
- `schema_version` MUST start with `aso-x.artifact_retention.`
- `retention_policy_id` MUST be a non-empty string
- `generated_at_utc` MUST be ISO-8601 UTC with trailing `Z`
- `source_repository` MUST be a non-empty string
- `branch` MUST be a non-empty string
- `commit` MUST be a lowercase 40-character hexadecimal Git SHA-1

## Retention rules
- `retention_class` MUST be one of:
  - `baseline`
  - `audit`
  - `release`
  - `security`
  - `durability`
- `default_retention` MUST be an object with:
  - `mode`
  - `minimum_years`
  - `immutable`
  - `review_cycle`
- `default_retention.mode` MUST be one of:
  - `retain`
  - `archive`
- `default_retention.minimum_years` MUST be an integer >= 1
- `default_retention.immutable` MUST be `true`
- `default_retention.review_cycle` MUST be one of:
  - `quarterly`
  - `semiannual`
  - `annual`

## Artifact inventory rules
- `artifacts` MUST be a non-empty list
- each entry MUST contain:
  - `name`
  - `path`
  - `category`
  - `retention_years`
  - `immutable`
  - `required_for_audit`
  - `required_for_release`
  - `notes`
- `path` MUST be a safe repository-relative path
- `category` MUST be one of:
  - `release-evidence`
  - `supply-chain`
  - `sbom`
  - `provenance`
  - `policy`
  - `test`
  - `documentation`
- `retention_years` MUST be an integer >= 1
- `immutable` MUST be `true`
- `required_for_audit` MUST be boolean
- `required_for_release` MUST be boolean
- `notes` MUST be a non-empty string

## Review rules
- `review` MUST be an object with:
  - `owner`
  - `last_reviewed_at_utc`
  - `next_review_due_utc`
  - `review_status`
- `owner` MUST be a non-empty string
- both review timestamps MUST be ISO-8601 UTC with trailing `Z`
- `next_review_due_utc` MUST be greater than or equal to `last_reviewed_at_utc`
- `review_status` MUST be one of:
  - `current`
  - `scheduled`

## Cross-baseline links
The artifact MUST include safe repository-relative paths to:
- `release_evidence_bundle_path`
- `supply_chain_integrity_path`
- `sbom_path`
- `provenance_attestation_path`

## Validation and mutability constraints
- `network_free_validation` MUST be `true`
- `mutable_external_sources_allowed` MUST be `false`
- `policy_audit_passed` MUST be `true`

## Validation evidence
`validation_evidence` MUST contain:
- `validator_command`
- `test_command`
- `validator_exit_code`
- `test_exit_code`

Both exit codes MUST equal `0`.

## Repository safety
All paths in this baseline MUST be repository-relative, must not be absolute,
must not use Windows drive prefixes, and must not escape the repository via `..`.

## Enforcement expectation
This baseline is deterministic, network-free at validation time, and intended
to support long-horizon evidence durability for ASO-X.