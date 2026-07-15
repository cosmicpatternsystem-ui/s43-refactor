# Evidence Contract Reconciliation Plan

Status: Active
Date: 2026-07-14
Authority: `docs/engineering-notes/evidence-contract-authority-decision.md`

## Objective

Reconcile evidence schema, runtime writer, tests, and examples so the repository has one enforceable evidence-record contract.

## Phase 1: Verify canonical schema details

Required direct verification items:

- Read `src/schemas/evidence-record.schema.json`
- Read `evidence_pack/schemas/evidence-record.schema.json`
- Confirm exact `required` fields
- Confirm `payload_hash` validation rule
- Confirm `additionalProperties`
- Confirm whether signature fields exist in schema and whether they are required

Exit criteria:

- A field-by-field comparison matrix exists
- The canonical schema behavior is known exactly
- Any remaining ambiguity is documented as a defect

## Phase 2: Collapse schema authority

Tasks:

- Make `src/schemas/evidence-record.schema.json` the sole schema authority
- Convert `evidence_pack/schemas/evidence-record.schema.json` into either:
  - an exact synchronized mirror, or
  - a deprecated path slated for removal
- Update package-local tests so they validate the canonical contract, not an independently drifting copy
- Remove ambiguous documentation references to `/schemas/evidence-record.schema.json` unless the path resolves uniquely

Exit criteria:

- No independently authoritative duplicate schema remains
- Tests across root and evidence-pack validate the same contract

## Phase 3: Align runtime writer

Tasks:

- Review `src/security/evidence_writer.py`
- Replace payload-oriented required-field assumptions if the canonical contract is hash-oriented
- Ensure emitted records align with canonical names, including:
  - `evidence_id`
  - `timestamp`
  - `event_type`
  - `provider_id`
  - `payload_hash`
- If backward compatibility is required, add an explicit adapter layer rather than silently accepting legacy field names

Exit criteria:

- Writer output validates against the canonical schema
- Legacy-field handling is explicit, documented, and tested

## Phase 4: Tighten validation

Tasks:

- Explicitly define `additionalProperties`
- Prefer `additionalProperties: false` unless there is a documented extensibility mechanism
- Enforce canonical `payload_hash` format:
  - `sha256:<64 lowercase hex>`
- Add negative tests for rejection of:
  - bare 64-character hashes
  - `payload` when only `payload_hash` is allowed
  - `uuid` when only `evidence_id` is allowed
  - `producer` when only `provider_id` is allowed
  - unexpected extra top-level fields if schema is closed

Exit criteria:

- Schema behavior is strict, deterministic, and test-covered

## Phase 5: Separate examples from runtime artifacts

Tasks:

- Classify `artifacts/evidence/record.json` as generated/runtime
- Maintain canonical samples under a dedicated examples path
- Ensure docs do not present generated runtime artifacts as normative samples

Exit criteria:

- Example files and runtime outputs have distinct roles
- Documentation is unambiguous

## Recommended test additions

- Canonical hash-format acceptance test
- Bare-hash rejection test
- Legacy-field rejection test
- Additional-properties rejection test
- Writer output schema-validation test
- Example-file schema-validation test

## Risks if deferred

- Schema drift between runtime and package-local validation
- Writer output that does not satisfy declared contract
- Acceptance of legacy or unintended fields
- Audit ambiguity about which evidence format is authoritative
- Confusion between runtime outputs and normative examples