# Release Audit Trail Policy

## Purpose
The release audit trail must provide a durable, reviewable, machine-checkable record of release governance activity.
It exists to support enterprise-grade operations, real-money resilience, incident analysis, and long-horizon repository integrity.

## Requirements
1. Every production-facing release process must produce an audit artifact.
2. The audit artifact must be stored as BOM-free UTF-8 with LF line endings.
3. The artifact must be repository-safe and deterministic in structure.
4. The artifact must be JSON and must conform to the required schema contract enforced by repository tests.
5. The artifact must include, at minimum:
   - schema_version
   - release_id
   - generated_at_utc
   - branch
   - commit
   - policy_audit_passed
   - checks
   - approvers
6. `policy_audit_passed` must be boolean.
7. `checks` must be a non-empty array of objects with:
   - name
   - status
8. `approvers` must be an array. It may be empty for sample artifacts, but the field must exist.
9. `branch` must not be empty.
10. `commit` must not be empty.
11. `schema_version` must begin with `aso-x.release_audit_trail.`

## Operational Rules
- The repository remains source-of-truth.
- Direct push to `main` remains prohibited by governance.
- Audit artifacts complement PR review and safe merge controls; they do not replace them.
- Any schema evolution must be backward-reviewed and tested.

## Validation
Audit artifacts are validated by `tools/release_audit_trail_check.py` and enforced by repository tests.
