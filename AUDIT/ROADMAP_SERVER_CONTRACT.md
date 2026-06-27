# Roadmap Server Contract

## Purpose

This document defines the future server-side contract expectations for synchronizing, indexing, displaying, or auditing the operational roadmap.

## Contract Status

This is a forward-compatible documentation contract. It does not activate a server integration and does not require a live server.

## Source Of Truth

The source of truth remains:

- PHASE_*.md files for phase-level source metadata.
- ROADMAP_CURRENT.json for generated roadmap state.
- scripts/update-roadmap.ps1 for roadmap generation.
- scripts/validate-roadmap.ps1 for schema validation.

## Read Model

A future server or dashboard may consume:

- schema_version
- enforcement_model
- generated_by
- phase_count
- generated_at
- phases

Each phase record may expose:

- file
- status
- documentation_only
- owner
- priority
- depends_on
- acceptance_criteria
- evidence
- last_verified_at
- future enterprise metadata fields once approved

## Write Model

Direct server-side mutation of generated roadmap state is not permitted unless a dedicated synchronization protocol is approved.

Any future write flow must:

- preserve source-file authority
- regenerate ROADMAP_CURRENT.json from source files
- pass validation gates
- produce auditable diffs
- retain CI enforcement compatibility

## Error States

A future server integration should detect and report:

- stale generated roadmap
- invalid schema version
- missing required metadata
- broken dependencies
- empty evidence
- empty acceptance criteria
- invalid lifecycle status
- missing verification timestamp


## Durable Automation And Continuity Controls

The roadmap governance system must expose machine-readable durable automation goals in the canonical roadmap JSON.

Minimum required controls:

- repository-only source of truth declaration
- crash-safe persistence and recovery semantics
- automated validation on pull request and push to main
- concurrent edit protection
- immutable auditability
- verified backup and restore procedures
- chat-memory-independent operation

A roadmap phase cannot claim real-money-safe or commercial-grade readiness unless these controls are declared, validated, and continuously enforced.

## Security And Safety
The roadmap server contract must not expose secrets, credentials, wallet material, private keys, tokens, or production-only operational data.

## Compatibility Statement

This contract is designed to be compatible with the existing generated-and-diff-enforced roadmap model.

## Safety Statement

This document is documentation-only. It does not connect to a server, modify runtime behavior, or change production execution logic.
