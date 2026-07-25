ROADMAP_CANONICAL.md is the human-readable canonical roadmap.
Canonical human source: `ROADMAP_CANONICAL.md`
Canonical machine source: `ROADMAP_CURRENT.json`
`$json_sha = cdde2a5b7c7520f81c503abb61ef617636774c3e098c9445390611c65ffce016`
Authority: canonical human
Independent authority: true


<!-- ASOX:CANONICAL_HUMAN_METADATA:START -->
Canonical human source: `ROADMAP_CANONICAL.md`
Canonical machine source: `ROADMAP_CURRENT.json`
`$json_sha = cdde2a5b7c7520f81c503abb61ef617636774c3e098c9445390611c65ffce016`
<!-- ASOX:CANONICAL_HUMAN_METADATA:END -->
<!-- Governance identity: This file is the human-readable canonical roadmap. -->
# ROADMAP_CANONICAL

This document is the canonical human-governed roadmap authority for ASO-X.

## Binding rules
## Binding rules
- Repo + GitHub are the operational source of truth.
- `docs/governance/ROADMAP_CANONICAL.md` defines canonical roadmap intent, release policy, and roadmap authority.
- `docs/governance/ROADMAP_MANIFEST.json` defines generator and enforcement relationships for roadmap artifacts.
- `docs/governance/ROADMAP_CURRENT.json` is the canonical machine-readable roadmap authority for operational consumption, but it is generated from this file and must remain a semantically equivalent machine-readable projection of this canonical authority.
- Any drift, shadow authority, invalid schema, BOM, CRLF/CR line ending, or unregistered governance asset is release-blocking.

## Mandatory execution order
## Mandatory execution order
1. P0-ROADMAP-AUTHORITY
2. P0-POLICY-TRIAD
3. P0-EVIDENCE-INTEGRITY
4. P1-OPS-REMEDIATION
5. P2-COMMERCIAL-VALIDATION

## Status model
## Status model
- PROPOSED
- APPROVED
- IMPLEMENTED
- VERIFIED
- INDEPENDENTLY_VERIFIED
- COMMERCIALLY_VALIDATED
- REJECTED

## Decision rule
## Decision rule
## Current Phase
- Phase: Operational Intelligence Runtime
- Task: MCP03 Invariants Formalization
## Current Next Action
Formalize MCP03_INVARIANTS.md and implement validation logic.
