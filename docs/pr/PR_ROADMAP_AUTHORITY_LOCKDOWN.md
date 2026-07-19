## Summary
Harden roadmap governance by removing executable shadow authority references to ROADMAP_CURRENT.json and enforcing the canonical authority path at:

- docs/governance/ROADMAP_CURRENT.json
"@

Write-Utf8NoBomLfFile G:\s43_work\s43_g11_work\docs\pr\RELEASE_NOTE_ROADMAP_AUTHORITY_LOCKDOWN.md @"
### Governance Hardening
Enforced canonical roadmap authority usage for ROADMAP_CURRENT.json by removing executable shadow-path references and adding enforcement to prevent regressions.