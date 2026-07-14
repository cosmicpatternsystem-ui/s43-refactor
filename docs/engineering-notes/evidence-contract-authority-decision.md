# Evidence Contract Authority Decision

Status: Accepted
Date: 2026-07-14
Owner: ASO-X engineering
Scope: Evidence record schema authority, runtime writer alignment, artifact classification

## Context

Repository evidence indicates a governance mismatch in the evidence contract:

- Runtime-oriented tests load `src/schemas/evidence-record.schema.json`.
- Evidence-pack tests load `evidence_pack/schemas/evidence-record.schema.json`.
- Documentation refers to `/schemas/evidence-record.schema.json`, which is ambiguous in the presence of multiple schema copies.
- Runtime writer logic still depends on a legacy payload-oriented model.
- Evidence-pack contract excerpts require an id/hash/provider-oriented model.
- Documentation and root tests use a prefixed hash format, while at least one evidence-pack test fixture uses a bare 64-character hash.

This creates ambiguity in schema authority, validation behavior, and writer compatibility.

## Decision

The canonical evidence-record schema authority for runtime and governance is:

- `src/schemas/evidence-record.schema.json`

The following policy decisions apply:

1. `src/schemas/evidence-record.schema.json` is the source of truth for the evidence-record contract.
2. `evidence_pack/schemas/evidence-record.schema.json` must not evolve independently.
3. Any schema copy under `evidence_pack/` is either:
   - a synchronized mirror of the canonical schema, or
   - a deprecated compatibility artifact pending removal.
4. The canonical `payload_hash` format is:
   - `sha256:<64 lowercase hex>`
5. `artifacts/evidence/record.json` is classified as a generated runtime artifact, not a canonical sample.
6. Canonical documentation examples must live under a separately named example path, such as:
   - `artifacts/examples/evidence_record.example.json`
7. The evidence writer must be aligned to the canonical schema contract and must not remain payload-oriented if the canonical schema is hash-oriented.
8. The canonical schema must explicitly define `additionalProperties` rather than relying on JSON Schema defaults.

## Rationale

This decision follows repo-first authority signals:

- Root tests and writer tests load the `src` schema path.
- Runtime governance should be anchored to the schema used by runtime-adjacent validation, not to generated artifacts or package-local duplicates.
- A prefixed hash format is already reflected in runtime-oriented documentation and tests.
- Generated artifacts under `artifacts/evidence/` should not act as normative contract sources.

## Consequences

Positive:

- Removes ambiguity about the source of truth.
- Creates a clear migration target for writer and tests.
- Separates canonical examples from runtime outputs.
- Enables stricter validation and better auditability.

Required follow-up:

- Reconcile `evidence_pack` schema/tests with the canonical `src` schema.
- Migrate writer-required fields from legacy payload-based expectations to the canonical evidence record model.
- Explicitly set `additionalProperties` in the canonical schema.
- Add negative tests for legacy-field rejection and hash-format enforcement.

## Known Unverified Items

The following items require direct repository-file verification before code changes are merged:

- Exact full `required` list in `src/schemas/evidence-record.schema.json`
- Actual `pattern` or equivalent validation rule for `payload_hash`
- Presence and value of `additionalProperties`
- Exact signature-field schema semantics, if any
- Whether `evidence_pack` should mirror or be removed entirely

Until those file contents are directly revalidated, this decision record governs authority and migration direction, not line-level implementation details.