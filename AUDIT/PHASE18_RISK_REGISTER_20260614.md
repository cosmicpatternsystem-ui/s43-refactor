# Phase 18 Risk Register - 2026-06-14

## Risk Policy

Every commercial release candidate risk must be either resolved, mitigated, accepted, or blocked before a release candidate tag is created.

## Open Risks

| ID | Risk | Severity | Status | Required Action |
| --- | --- | --- | --- | --- |
| R18-001 | Manual push bypasses approved sync | High | Mitigated | Continue using tools/phase17_approved_sync.ps1 only |
| R18-002 | Feature work enters release candidate baseline | High | Open | Enforce Phase 18 feature freeze |
| R18-003 | Dirty working tree before sync | High | Mitigated | Allow only explicit Phase 18 files before sync |
| R18-004 | Branch drift from official baseline | High | Mitigated | Validate branch before every protected operation |
| R18-005 | Missing release readiness evidence | Medium | Open | Complete checklist before RC tag |
| R18-006 | Unreviewed critical asset changes | High | Open | Stage explicit paths only through approved sync |
| R18-007 | Recovery path not verified before release candidate | Medium | Open | Confirm rollback and snapshot documentation |
| R18-008 | Encoding/path issues on Windows PowerShell | Medium | Mitigated | Use UTF-8 console setup and literal repo path |
| R18-009 | False success marker after failed sync | High | Mitigated | Print PASS only after post-sync HEAD/origin/clean verification |

## Critical Assets

- tools/phase17_approved_sync.ps1
- tools/enterprise_quality_gate_phase17.ps1
- tools/phase17_worker_health_check.ps1
- tools/safe_auto_snapshot_phase17.ps1
- ROADMAP/COMMERCIAL_MASTER_ROADMAP_20260614.md
- ROADMAP/PHASE18_COMMERCIAL_RELEASE_CANDIDATE_PLAN_20260614.md
- AUDIT/PHASE17_OPERATIONAL_READINESS_BASELINE_20260614.md
- AUDIT/PHASE18_RELEASE_READINESS_CHECKLIST_20260614.md
- AUDIT/PHASE18_RISK_REGISTER_20260614.md
- AUDIT/PHASE18_ONE_COPY_PASTE_AUTOMATION_STANDARD_20260614.md
- AUDIT/PHASE18_OPENING_AUTOMATION_VERIFICATION_20260614.md
- ARCHIVE/PHASE17_SNAPSHOT_AND_ARCHIVE_MANIFEST_20260614.md

## Release Candidate Blocking Conditions

- Quality gate failure
- Health check failure
- Approved sync failure
- Dirty working tree after sync
- HEAD not equal to origin/phase17-work-from-restore
- Unresolved critical risk without written acceptance
- Manual push outside approved sync
- New feature work mixed into release hardening
- False pass marker without verified sync
