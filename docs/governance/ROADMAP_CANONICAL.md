# ROADMAP_CANONICAL

This document is the canonical human-governed roadmap authority for ASO-X.

## Binding rules

- Repo + GitHub are the operational source of truth.
- `docs/governance/ROADMAP_CANONICAL.md` defines canonical roadmap intent, release policy, and roadmap authority.
- `docs/governance/ROADMAP_MANIFEST.json` defines generator and enforcement relationships for roadmap artifacts.
- `docs/governance/ROADMAP_CURRENT.json` is a generated machine-readable projection and must remain semantically equivalent to this file.
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

## 4. Roadmap Authority Model

This file is the canonical human-governed roadmap authority for ASO-X.

Authority order:

1. `docs/governance/ROADMAP_CANONICAL.md` defines canonical roadmap intent, release policy, and roadmap authority.
2. `docs/governance/ROADMAP_MANIFEST.json` defines generator and enforcement relationships for roadmap artifacts.
3. `docs/governance/ROADMAP_CURRENT.json` is a generated projection derived from canonical repository state and is not independently authoritative.
4. Merged PR state is the implementation record and evidence trail, not the roadmap authority.
5. Issues, notes, and discussion artifacts are context only unless promoted into canonical roadmap authority by protected PR approval.

Repository roadmap truth must not be inferred from issues, branch-local notes, or generated files when that truth conflicts with this document.

## 5. MCP-02 Canonical Definition

`MCP-02` is the first buyer-credible, evidence-backed Decision API slice for ASO-X.

The product rule for `MCP-02` is `domain-open but outcome-closed`:

- The domain remains open until protected PR approval locks the first production slice.
- The release outcome is fixed now: ASO-X must ship the smallest commercially meaningful decision slice that preserves determinism, explainability, auditability, and replayability.

### MCP-02 Release Constraints

The first `MCP-02` release must satisfy all of the following:

1. Exactly one event class is allowed in the initial release.
2. Output must be machine-readable.
3. Output must include stable reason codes.
4. Output must include evidence links or evidence references that are durable and auditable.
5. Deterministic replay on fixed fixtures is mandatory.
6. Incomplete, malformed, or untrusted input must fail closed.
7. The output contract must remain bounded and reviewable.
8. Domain lock requires protected PR approval.

### Domain Lock Prerequisites

The `MCP-02` domain must not be locked until the protected PR includes all of the following:

1. Buyer problem statement with explicit commercial relevance.
2. Single event class definition.
3. Bounded output contract with machine-readable decision fields.
4. Replayable fixture pack.
5. Benchmark evidence.
6. Legal and compliance note appropriate to the selected domain.
7. Evidence-backed reason code set.
8. Explicit rollback and risk note.

### Evidence Pack Requirement

Any PR that changes behavior, contract, replay semantics, evidence format, or reason codes for active MCP delivery must include a behavior change evidence pack.

Mandatory evidence pack contents:

- fixtures
- fixture hashes or equivalent integrity metadata
- replay result
- contract diff
- benchmark evidence
- audit log or evidence reference
- rollback and risk notes
- governance validation output
- migration notes when versioning applies
- reason code and evidence retention notes when behavior changes affect explainability

Recommended evidence pack contents:

- reviewer checklist
- cross-platform replay result
- negative test summary
- performance delta
- buyer-facing output example

### Breaking Change Policy

No breaking changes may land on `main` for active roadmap contracts without explicit roadmap authority approval in a protected PR.

Breaking changes include, at minimum, changes to:

- schema
- output contract
- reason codes
- evidence format
- replay behavior
- validation semantics that affect fail-closed behavior

Approved breaking changes must include:

- explicit versioning
- migration plan
- replay evidence
- contract impact summary
- approval in the protected PR record

### Stop Rules

Merge or release activity must pause when any of the following is true:

1. Deterministic replay regresses on fixed fixtures.
2. Required evidence links or reason codes are missing from decision output.
3. Fail-closed validation is weakened or bypassed.
4. A behavior-changing PR lacks the required evidence pack.
5. Governance work expands without directly protecting active MCP delivery.
6. No protected PR locks the `MCP-02` domain by the declared domain selection deadline.

### Anti-Scope-Drift Rule

During `MCP-02` domain selection and first-slice delivery, new governance work is allowed only when it directly protects active revenue-relevant product delivery.

Allowed governance work includes only delivery-critical controls such as:

- replay protection
- evidence immutability
- contract validation
- CI integrity
- authority enforcement

Governance expansion that does not directly support active MCP delivery is out of scope for this phase.

## 6. Successor Governance Target

The immediate successor authority target after `MCP-02` is `MCP-03: Formalized Successor Governance`.

`MCP-03` exists to formalize how roadmap authority advances after protected completion of an active MCP slice without introducing shadow authority, ambiguous successor selection, or generated-file-first governance.

### MCP-03 Scope

`MCP-03` is limited to the following governance outcomes:

1. Define an explicit canonical successor-selection rule for roadmap advancement.
2. Require that successor authority transitions are declared first in `docs/governance/ROADMAP_CANONICAL.md`.
3. Require that generated roadmap artifacts remain projections and never become independent authority during handoff.
4. Define the minimum evidence required to mark a roadmap item governed-complete and activate its successor.
5. Preserve protected-PR approval, auditability, deterministic validation, and fail-closed governance behavior.

### MCP-03 Non-Scope

`MCP-03` does not authorize:

- domain lock changes for `MCP-02`
- product-scope expansion unrelated to active delivery protection
- generated-file-only roadmap edits
- successor inference from local notes, issue threads, or other non-canonical artifacts

### Successor Activation Rule

A successor roadmap authority target may become active only when all of the following are true:

1. The predecessor state and closeout evidence are declared in canonical form.
2. The successor is named explicitly in `docs/governance/ROADMAP_CANONICAL.md`.
3. The transition is approved in a protected PR.
4. Generated roadmap artifacts are regenerated after the canonical update.
5. Validation confirms semantic alignment between canonical and generated roadmap artifacts.

### MCP-02 Closeout Requirement For Successor Activation

`MCP-02` must not hand off roadmap authority to `MCP-03` unless the protected PR record includes, at minimum:

- closeout timestamp
- governing PR reference
- validation result
- evidence pack reference
- explicit successor declaration
- rollback or reopen criteria if closeout assumptions later fail
