# Agent Runbook

## Purpose
This runbook allows any future agent to continue the project without relying on chat history or undocumented operator knowledge.

## Source Of Truth
1. Git repository state on the active branch
2. `OPERATING_STANDARD.md`
3. `AUDIT/NEXT_ACTION.md`
4. `AUDIT/COMMERCIAL_MANDATORY_ROADMAP.md`
5. The latest validated disaster recovery backup

## Mandatory Completion Workflow
No material change is complete until the agent runs:

    .\tools\Invoke-SafeSyncAndBackup.ps1 -CommitMessage "<completed change>"

The agent must not declare completion unless the workflow ends with:
- tests passing
- git whitespace checks passing
- commit created
- push succeeded
- workspace clean
- remote synced
- DR backup created

## Standard Session Flow
1. Open the repository root.
2. Read the operating standard and audit files.
3. Inspect current branch and workspace state.
4. Make the required change.
5. Run validation.
6. Execute the official safe sync and DR backup workflow.
7. Report final branch, commit, upstream, test result, and backup path.

## Required Final Report Fields
- branch
- final commit hash
- upstream
- backup path
- test result
- workspace status
- remote sync status

## If Execution Access Is Available
The agent is responsible for performing the change, validation, commit, push, and backup workflow directly.

## If Execution Access Is Not Available
The agent must not claim execution occurred. The agent must explicitly state the limitation and provide the exact command sequence required for completion.

## Prohibited Behavior
- treat chat-only planning as completed work
- claim push or backup success without execution evidence
- mark meaningful work complete with a dirty workspace
- bypass the official sync and DR backup workflow for major changes

## Handoff Rule
A future agent must be able to continue the project using only the repository, the committed documentation, and the latest validated backup artifacts.
