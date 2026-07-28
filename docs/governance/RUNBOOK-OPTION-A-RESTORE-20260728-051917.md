# Runbook Option A - Restore Record

- runbook_id: RUNBOOK-OPTION-A-RESTORE-20260728-051917
- runbook_date_utc: 2026-07-28
- operator: S.Saead Lajevardy
- branch: task/33-01-01-ci-gate-hardening
- baseline_head_before_restore: 164d6b48

## Scope

Restore executed under ratified Option A governance path.

Retained authority path:
- `scripts/update-roadmap.ps1`

This step restores approved contract-sensitive files to HEAD.

## Restored Targets
- `docs/governance/ROADMAP_CURRENT.json`
- `scripts/check_evidence_gate.py`
- `scripts/roadmap_generator.py`
- `scripts/validate-roadmap.ps1`

## Explicit Non-Targets
- `scripts/update-roadmap.ps1`
- `closure_signoff.ps1`
- `EVIDENCE_*`
- `_evidence/`

## Verification
- restore_source: HEAD
- restore_verification: PASS
- residual_modification_on_restored_targets: NO

## Outcome
- restore_result: SUCCESS
- follow_on_step: VERIFY
- authority_mutation_performed: NO
- evidence_preserved: YES