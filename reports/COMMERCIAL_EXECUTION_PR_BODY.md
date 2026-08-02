## Summary
- add a production-safe commercial execution gate runner for PowerShell 5.1
- finalize minimal roadmap remediation required for commercial execution gate evaluation
- add PR evidence artifacts documenting gate outcome and remediation lineage

## Included Changes
- update `docs/governance/ROADMAP_CURRENT.json`
- add `scripts/commercial_execution_gate_runner.ps1`
- add `scripts/build_commercial_gate_pr_evidence.ps1`
- add `reports/COMMERCIAL_EXECUTION_PR_EVIDENCE_SUMMARY.md`
- add `reports/COMMERCIAL_EXECUTION_PR_BODY.md`

## Validation
- final commercial execution gate verdict: `GO`
- final posture: `UNBLOCKED`
- gates passed: `scope=true`, `governance=true`, `structure=true`, `financial_relevance=true`
- blocking findings: `0`
- warnings: `0`
- final validation evidence recorded in `reports/COMMERCIAL_EXECUTION_GATE_REPORT_20260802_053057.json`

## Evidence Lineage
- `reports/ROADMAP_MINIMAL_REMEDIATION_PATCH_REPORT_20260802_050836.json`
- `reports/ROADMAP_MINIMAL_REMEDIATION_PATCH2_REPORT_20260802_051211.json`
- `reports/ROADMAP_CRLF_NORMALIZATION_RETRY_REPORT_20260802_052037.json`
- `reports/COMMERCIAL_EXECUTION_GATE_REPORT_20260802_051440.json`
- `reports/COMMERCIAL_EXECUTION_GATE_REPORT_20260802_053057.json`

## Risk Notes
- fail-closed behavior is preserved
- no scope expansion was introduced
- unrelated local dirty/untracked files were intentionally excluded from this PR