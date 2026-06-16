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
