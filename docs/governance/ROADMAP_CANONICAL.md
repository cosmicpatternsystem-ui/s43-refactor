# ROADMAP_CANONICAL

This document is the human-readable rendering of `docs/governance/ROADMAP_CURRENT.json`.

## Binding rules

- Repo + GitHub are the operational source of truth.
- `docs/governance/ROADMAP_CURRENT.json` is the canonical machine-readable roadmap authority.
- This file must remain semantically equivalent to `ROADMAP_CURRENT.json`.
- Any drift, shadow authority, invalid schema, BOM, CRLF/CR line ending, or unregistered governance asset is release-blocking.

## Mandatory execution order

1. P0-ROADMAP-AUTHORITY
2. P0-POLICY-TRIAD
3. P0-EVIDENCE-INTEGRITY
4. P1-OPS-REMEDIATION
5. P2-COMMERCIAL-VALIDATION

## Status model

- PROPOSED
- APPROVED
- IMPLEMENTED
- VERIFIED
- INDEPENDENTLY_VERIFIED
- COMMERCIALLY_VALIDATED
- REJECTED

## Decision rule

No evidence, no DONE.
