# ASO-X Evidence Record Format

## Purpose

The Evidence Record format defines the mandatory, versioned, machine-validatable structure used to retain operational, governance, CI, artifact, release, and policy evidence for ASO-X.

## Authority

This format supports the ASO-X integrated mandatory roadmap and is part of the durable intelligence operating layer.

## Design Requirements

- Versioned schema
- Machine validation
- Human readability
- 50-year durability
- Cryptographic agility
- Artifact retention support
- Policy-driven governance
- Repository-first source of truth
- Backward-compatible evolution

## Current Schema Version

`1.0.0`

## Required Fields

- `schema_version`
- `evidence_id`
- `evidence_type`
- `created_at`
- `producer`
- `subject`
- `summary`
- `integrity`
- `retention`

## Evidence Types

- `commit`
- `pull_request`
- `ci_run`
- `artifact`
- `policy_decision`
- `roadmap_milestone`
- `release_gate`
- `security_validation`
- `operator_action`
- `automation_run`

## Retention Classes

- `temporary`
- `standard`
- `long_term`
- `permanent`

## Cryptographic Agility

The schema intentionally separates:

- hash algorithm
- canonicalization method
- content hash
- optional signature metadata

This allows future migration from classical algorithms to post-quantum or hybrid cryptographic schemes without changing the evidence model.

## Compatibility Rules

Schema `1.0.0` records must remain readable and valid under their original schema version.

Future versions must not silently reinterpret historical records.

## Validation

Evidence records must validate against:
```text
schemas/evidence-record.schema.json

## Minimal Example

json
{
  "schema_version": "1.0.0",
  "evidence_id": "evd_p32_minimal_0001",
  "evidence_type": "roadmap_milestone",
  "created_at": "2026-07-05T00:00:00Z",
  "producer": {
"type": "automation",
"name": "aso-x"
  },
  "subject": {
"repo": "cosmicpatternsystem-ui/s43-refactor",
"ref": "P3.2"
  },
  "summary": "Evidence record schema introduced for ASO-X P3.2.",
  "integrity": {
"hash_algorithm": "none",
"canonicalization": "none"
  },
  "retention": {
"class": "permanent",
"minimum_years": 50,
"immutable": true,
"reason": "Governance evidence for the ASO-X durable roadmap."
  }
}
