# P2.7 SBOM Baseline Policy

## Purpose

This policy defines the repository baseline for Software Bill of Materials
(SBOM) evidence in ASO-X.

The purpose of this baseline is to provide a deterministic, reviewable, and
network-free SBOM artifact contract that can be validated in CI and connected
to release evidence and supply-chain integrity governance.

## Scope

This baseline covers:

- the required repository SBOM policy;
- a sample SBOM audit artifact;
- a deterministic validator;
- positive and negative tests for the SBOM contract.

This baseline does not claim to implement complete package ecosystem discovery,
cryptographic provenance, registry verification, external vulnerability
scanning, or full third-party SBOM generation.

Those capabilities may be added in later phases. This phase establishes the
minimum durable repository contract.

## Required Artifact Fields

An SBOM artifact MUST contain these top-level fields:

- `schema_version`
- `sbom_id`
- `generated_at_utc`
- `source_repository`
- `branch`
- `commit`
- `format`
- `components`
- `supply_chain_integrity_path`
- `release_evidence_bundle_path`
- `network_free_validation`
- `mutable_external_sources_allowed`
- `policy_audit_passed`
- `validation_evidence`

## Field Rules

### schema_version

The schema version MUST start with:
```text
aso-x.sbom.

The initial baseline schema is:

text
aso-x.sbom.v1

### sbom_id

The SBOM ID MUST be a non-empty string.

It SHOULD be stable enough to identify the audit artifact in review logs.

### generated_at_utc

The generation timestamp MUST be an ISO-like UTC timestamp ending in `Z`.

Example:

text
2026-07-05T06:05:00Z

### source_repository

The source repository MUST be a non-empty string.

### branch

The branch MUST be a non-empty string.

For release-bound samples, this SHOULD normally be `main`.

### commit

The commit MUST be a lowercase 40-character SHA-1 commit ID.

Short hashes are not accepted in SBOM audit artifacts.

### format

The SBOM format MUST be one of:

- `aso-x-minimal`
- `cyclonedx-json`
- `spdx-json`

The initial repository baseline uses `aso-x-minimal`.

### components

The components field MUST be a non-empty list.

Each component MUST include:

- `name`
- `type`

Each component MUST also include either:

- `version`

or:

- `version_status`

The component type MUST be one of:

- `application`
- `library`
- `runtime`
- `tooling`
- `manifest`
- `lockfile`
- `documentation`
- `policy`
- `test`

A component MAY include a relative repository path through the `path` field.

If present, component paths MUST be repository-relative paths. Absolute paths
and parent-directory traversal are forbidden.

### supply_chain_integrity_path

The supply-chain integrity path MUST be a non-empty repository-relative path.

It SHOULD normally point to:

text
docs/security/audit/sample-supply-chain-integrity.json

### release_evidence_bundle_path

The release evidence bundle path MUST be a non-empty repository-relative path.

It SHOULD normally point to:

text
docs/release/audit/sample-release-evidence-bundle.json

### network_free_validation

This MUST be `true`.

SBOM baseline validation must not depend on network access.

### mutable_external_sources_allowed

This MUST be `false`.

The baseline does not permit mutable external source references as authoritative
SBOM evidence.

### policy_audit_passed

This MUST be `true`.

A sample artifact must explicitly state that it conforms to this policy.

### validation_evidence

The validation evidence object MUST include:

- `validator_command`
- `test_command`
- `validator_exit_code`
- `test_exit_code`

Both exit codes MUST be `0`.

## Repository Safety

The SBOM validator MUST:

- avoid network access;
- avoid modifying repository files;
- use deterministic validation rules;
- report all validation errors found in a single pass where practical;
- return a non-zero exit code when validation fails.

## Relationship to P2.5 Release Evidence Bundle

P2.5 introduced a release evidence bundle baseline.

The SBOM baseline is complementary evidence. It records what software components
and repository artifacts are represented by the release and links back to the
release evidence bundle path.

## Relationship to P2.6 Supply Chain Integrity

P2.6 introduced a supply-chain integrity baseline.

The SBOM baseline links to the supply-chain integrity artifact so that release
review can connect component inventory evidence with source and dependency
integrity evidence.

## Operational Rule

A release or governance workflow MUST NOT treat an SBOM artifact as valid unless
the SBOM validator passes and the policy audit is true.