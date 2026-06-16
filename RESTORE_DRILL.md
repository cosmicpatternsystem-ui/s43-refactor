# Restore Drill

## Purpose
This document defines the mandatory disaster recovery restore drill for the project.
A backup is not fully trusted until it has been restored and validated on a separate path or machine.

## Required Backup Artifacts
- tracked_source.zip
- repo.bundle
- manifest.sha256
- artifacts.sha256
- status.json
- verification.txt
- RESTORE_INSTRUCTIONS.txt

## Mandatory Restore Drill Frequency
- after any major workflow change
- after backup format changes
- before major release or handoff
- whenever backup integrity is in doubt

## Restore Drill Procedure
1. Select a completed backup directory.
2. Create a clean restore target outside the main repository.
3. Verify artifact hashes.
4. Restore the Git history from `repo.bundle`.
5. Extract `tracked_source.zip`.
6. Compare restored state with recorded backup metadata.
7. Run project validation commands.
8. Record the outcome in the audit trail.

## Minimum Restore Validation
1. `repo.bundle` restores successfully.
2. `tracked_source.zip` extracts successfully.
3. `artifacts.sha256` validates successfully.
4. Restored HEAD matches the recorded commit.
5. Validation commands pass.
6. The result is documented.

## Failure Handling
1. The backup must not be treated as fully trusted.
2. The failure reason must be documented.
3. A corrected backup must be created.
4. A new restore drill must be completed.

## Completion Rule
No disaster recovery workflow is considered mature until at least one successful restore drill has been completed and documented from a real backup artifact set.

## Restore Drill Evidence - 20260616_232209

- backup_path: E:\saead\ssl\s43_project_backups\phase17-controlled-development_20260616_231529_dceee5f3b3c7
- restore_target: E:\saead\ssl\s43_restore_drills\restore_drill_20260616_232209
- source_commit: dceee5f3b3c7e97e435283ccd355399fba9a4319
- branch: phase17-controlled-development
- upstream: origin/phase17-controlled-development
- artifacts_sha256: passed
- repo_bundle_verify: passed
- bundle_clone: passed
- restored_head_match: passed
- tracked_source_extract: passed
- restored_pytest: passed
- result: validated

## Restore Drill Evidence - 20260616_233441

- backup_path: E:\saead\ssl\s43_project_backups\phase17-controlled-development_20260616_232541_e171b3754c12
- restore_target: E:\saead\ssl\s43_restore_drills\restore_drill_20260616_233441
- source_commit: e171b3754c1227e415399861d301208c3fd0a424
- branch: phase17-controlled-development
- upstream: origin/phase17-controlled-development
- artifacts_sha256: passed
- repo_bundle_verify: passed
- bundle_clone: passed
- restored_head_match: passed
- tracked_source_extract: passed
- restored_pytest: passed
- result: validated
