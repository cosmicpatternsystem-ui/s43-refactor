# Evidence Contract Alignment Verification

Date: 2026-07-14

Status: Completed

## Objective

Finalize contract alignment across the live Evidence system and eliminate residual legacy terminology.

Canonical field names:
- `event_type`
- `payload_hash`

Deprecated field names:
- `evidence_type`
- `content_hash`

## Scope

The live alignment covered:
- runtime code
- tests
- roadmap-related scripts
- live evidence artifacts

Historical audit snapshots under `artifacts/audits/` were intentionally excluded to preserve immutable historical evidence.

## Validation Summary

Completed checks:
- focused Evidence test execution
- full Evidence test suite execution
- residual legacy scan excluding historical audit snapshots
- governance pre-commit validation

Observed final results:
- focused tests passed
- full Evidence suite passed
- no live residual legacy terms found
- governance validation passed
- repository returned to a clean post-commit state

## Files Aligned

Representative live files aligned during this phase include:
- `src/security/evidence_writer.py`
- `asoctl.py`
- `scripts/atomic_roadmap_writer.py`
- `tests/test_evidence_integration.py`
- `tests/test_p35_commercial_positioning.py`
- `artifacts/evidence/record.json`
- `artifacts/evidence/p33/p33_live_test.json`
- `artifacts/evidence/p33/p33_missing_fields_result.json`
- `artifacts/evidence/commercial_positioning_decision.json`

## Encoding Correction

A UTF-8 BOM regression was detected in JSON artifacts after a PowerShell write path used BOM-producing UTF-8 output.

Resolution:
- all touched live files were rewritten as UTF-8 without BOM
- JSON parsing behavior was revalidated through test execution

## Outcome

The live Evidence surface is now aligned to the canonical contract and considered zero-legacy within active scope.

Boundary note:
- `artifacts/audits/` remains unchanged by design as immutable historical evidence

## Commit Lineage

- `7c60fda` `refactor(evidence): align records with canonical schema`
- `87456e5` `refactor(evidence): final contract alignment and path verification`
- `651ca24` `refactor(evidence): deep align live artifacts and roadmap hash contract`

## Follow-up Controls

To prevent regression:
- add a repository guard test that fails on `evidence_type`
- add a repository guard test that fails on `content_hash`
- exclude immutable historical audit snapshots from the guard scope