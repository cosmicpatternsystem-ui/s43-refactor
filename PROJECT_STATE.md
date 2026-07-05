# ASO-X Project State

Updated: 2026-07-05T19:13:14Z

## Current Governance State

- Canonical governance lock count: 32
- Source of truth: repository only
- Main branch changes: pull request only
- Continuity requirement: a new session must resume from committed repo artifacts

## Current Local Continuation Instruction

Run:
```powershell
python tools\project_status.py
python asoctl.py validate
python asoctl.py next
python -m pytest -q
