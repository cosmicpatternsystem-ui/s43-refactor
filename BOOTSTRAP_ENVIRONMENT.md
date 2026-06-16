# Bootstrap Environment

## Purpose
This document defines the minimum steps required to bring the project online on a new machine or in a fresh working environment.

## Required Inputs
- the Git repository remote
- the latest validated disaster recovery backup
- PowerShell
- Git
- Python
- pytest
- any required credentials for GitHub access

## Standard Bootstrap Procedure
1. Create a clean working directory.
2. Clone the repository from GitHub.
3. Switch to the required branch.
4. Verify the latest expected commit.
5. Install project dependencies.
6. Run the validation command set.
7. Confirm the official backup workflow script exists.
8. Read the operating and audit documents before making changes.

## Commands
```powershell
git clone git@github.com:cosmicpatternsystem-ui/s43-refactor.git
cd s43_refactor
git checkout phase17-controlled-development
git status --short
pytest -q
Get-ChildItem .\tools\Invoke-SafeSyncAndBackup.ps1

## Bootstrap From Backup If Remote Access Fails
1. Copy the backup set to the new machine.
2. Verify `artifacts.sha256`.
3. Restore Git history from `repo.bundle`.
4. Extract `tracked_source.zip`.
5. Verify the recorded HEAD from `status.json`.
6. Run validation commands.

## Minimum Ready State
1. The repository is present locally.
2. The correct branch is checked out.
3. The expected validation command passes.
4. The operating documents are available.
5. The backup workflow script is present and executable.

## First Action Rule
The first meaningful change on a new machine must still end with the official safe sync and disaster recovery workflow.
