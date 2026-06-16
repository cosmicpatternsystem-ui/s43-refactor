# Mandatory Autonomous Safe Sync And Disaster Recovery Policy

From this point forward, no material project change is considered complete until
the operating agent has executed the official safe sync and disaster recovery
workflow from the repository root:

    .\tools\Invoke-SafeSyncAndBackup.ps1 -CommitMessage "<completed change>"

The agent, not the user, is responsible for running this workflow whenever the
agent has executable access to the project environment.

A change may only be declared complete when all of the following are true:

1. Tests pass.
2. Git whitespace checks pass.
3. The change is committed to the active branch.
4. The commit is pushed to the configured upstream on GitHub.
5. The workspace is clean.
6. The remote is synced.
7. A physical disaster recovery backup is created.
8. The backup contains:
   - tracked_source.zip
   - repo.bundle
   - manifest.sha256
   - artifacts.sha256
   - status.json
   - verification.txt
   - RESTORE_INSTRUCTIONS.txt
9. The final response records:
   - branch
   - final commit hash
   - GitHub upstream
   - physical backup path
   - test result
   - workspace clean status
   - remote synced status

If executable access is unavailable, the agent must not claim the workflow was
completed. The agent must clearly state that execution access is unavailable and
provide the exact command sequence required to complete the operation.

This policy is mandatory and overrides informal summaries, chat-only assurances,
or partial completion statements.

## Definition Of Done

A meaningful change is done only when all of the following are true:

1. The intended change is implemented.
2. Required validation passes.
3. `git diff --check` passes.
4. The change is committed.
5. The change is pushed to the configured upstream.
6. The workspace is clean.
7. The remote is synced.
8. A disaster recovery backup is created with:
   - tracked_source.zip
   - repo.bundle
   - manifest.sha256
   - artifacts.sha256
   - status.json
   - verification.txt
   - RESTORE_INSTRUCTIONS.txt
9. The final report records branch, commit, upstream, backup path, and validation result.
