# Release Attestation Policy

## Purpose

This policy defines the baseline requirements for ASO-X release governance
attestation artifacts.

A release attestation is a repository-safe evidence document that binds a
release identifier to a branch, commit, audit artifact reference, audit artifact
hash, policy audit result, and attestors.

Release attestation is an evidence layer. It does not replace pull request
review, safe merge automation, policy audit, or any required human approval.

## Scope

This policy applies to production-facing ASO-X release governance evidence.

The P2.4 baseline defines the expected artifact shape, validation rules, and
repository-safety requirements. It does not introduce cryptographic signing,
external trust roots, or CI enforcement. Those capabilities may be introduced in
later phases.

## Artifact Requirements

A release attestation artifact MUST be JSON and MUST include these keys:

- `schema_version`
- `release_id`
- `attested_at_utc`
- `branch`
- `commit`
- `artifact_path`
- `artifact_sha256`
- `policy_audit_passed`
- `attestors`

The `schema_version` value MUST start with:
```text
aso-x.release_attestation.

The `commit` value MUST be a full 40-character hexadecimal SHA-1 commit id.

The `artifact_sha256` value MUST be a 64-character hexadecimal SHA-256 digest.

The `attestors` value MUST be a non-empty array of non-empty strings.

The `policy_audit_passed` value MUST be a JSON boolean.

## Repository Safety

Release attestation artifacts MUST be safe to store in the repository.

They MUST NOT contain:

- secrets
- credentials
- access tokens
- private keys
- personal access tokens
- environment-specific confidential values

Artifacts MUST be encoded as UTF-8 without BOM and use LF line endings.

## Determinism

Release attestation artifacts SHOULD be deterministic and reviewable.

Fields SHOULD use stable names and simple JSON-compatible values. The artifact
SHOULD avoid environment-dependent formatting, local machine paths, or
non-reproducible metadata.

## Relationship to Audit Trail

The attestation artifact SHOULD reference the associated audit trail artifact by
repository-relative path in `artifact_path`.

The `artifact_sha256` value records the expected SHA-256 digest for the referenced
audit artifact. The P2.4 baseline validates the digest format. Future phases may
verify the digest against the referenced file content.

## Operational Rule

A release attestation is valid only when it passes the repository validator and
is reviewed through the normal pull request and safe merge process.
