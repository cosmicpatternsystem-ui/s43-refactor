# Commercial Execution Gate Hardening + Roadmap Remediation Alignment

## Summary
This PR finalizes the commercial execution gate runner and aligns the roadmap target phase with enforcement expectations for commercial execution control.

## Scope
- Add production-safe PowerShell 5.1 gate runner
- Fix target phase lookup behavior against actual roadmap schema
- Preserve fail-closed gate semantics
- Align target phase structural metadata
- Preserve explicit financial relevance enforcement
- Normalize roadmap file formatting to UTF-8 without BOM and LF-only

## Key Fixes
- Check top-level `phases` before recursive fallback
- Support both `id` and `phase_id`
- Validate governance metadata:
  - `schema_version=2.0`
  - `source_of_truth=repository_files_only`
  - `enforcement_model=generated-and-diff-enforced-in-pr`
  - `canonical_roadmap=docs/governance/ROADMAP_CANONICAL.md`
- Validate target phase structure:
  - `owner`
  - `priority`
  - `last_verified_at`
  - non-empty `tasks`
- Validate explicit financial relevance through task / acceptance / evidence content
- Emit structured JSON report under `reports/`

## Final Result
- Verdict: `GO`
- Posture: `UNBLOCKED`
- Scope: `True`
- Governance: `True`
- Structure: `True`
- Financial relevance: `True`
- Findings: `0`
- Warnings: `0`

## Final Evidence
- `reports/COMMERCIAL_EXECUTION_GATE_REPORT_20260802_053057.json`
- `reports/COMMERCIAL_EXECUTION_GATE_REPORT_20260802_051440.json`
- `reports/ROADMAP_MINIMAL_REMEDIATION_PATCH_REPORT_20260802_050836.json`
- `reports/ROADMAP_MINIMAL_REMEDIATION_PATCH2_REPORT_20260802_051211.json`
- `reports/ROADMAP_CRLF_NORMALIZATION_RETRY_REPORT_20260802_052037.json`

## Risk / Controls
This change does not relax governance. It hardens enforcement by making lookup and validation consistent with the actual repository schema while preserving fail-closed behavior.