# PR #333 Root Cause And Remediation Ledger

## Status
FAIL-CLOSED / EVIDENCE-BOUND REMEDIATION

## Proven Evidence
- INV-MCP03-000 checks HEAD atomicity using `git diff-tree --no-commit-id --name-only -r HEAD`
- Artifacts checked: `docs/governance/ROADMAP_CANONICAL.md` and `docs/governance/ROADMAP_CURRENT.json`
- Failure condition: exactly one of the two artifacts changes
- SHA256 handling exists in the roadmap authority validator

## Rejected Claims
- No reliance on `git log -1` last-touch commit parity
- No reliance on unproven `canonical_md_hash` enforcement

## Added Controls
- `scripts/guard_pr333_governance_atomicity.py`
- `scripts/run_pr333_governance_guard.ps1`
- `.github/workflows/pr333-governance-guard.yml`
