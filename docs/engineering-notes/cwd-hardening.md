# CWD Hardening Regression Note
## Root Cause
Exec-And-Capture launched child processes without reliably applying WorkingDirectory.
## Remediation
- Added WorkingDirectory fallback to repoRoot in Exec-And-Capture.
- Hardened critical callsites in persist-governance-state.ps1.
- Added LF normalization rules in .gitattributes.
