# ASO-X Project Handoff

**Date:** 2026-07-03  
**Phase:** A (governance) → B1 (durability)  
**Branch:** main  
**Last Commit:** 2f4d7fd - chore: ignore backup and patch-log artifacts (#191)

## Mission
**Global Financial Intelligence** — enterprise-grade system with50-year durability target.

## Current State
### Blocking Issues
1. **source_of_truth mismatch**- ROADMAP_CURRENT.json says: `"repository phase documents"`
   - roadmap_guard.py expects: `"repository_files_only"`
   - **Action:** Canonicalize to `repository_files_only`

2. **PR #190 conflicts**
   - Merge conflicts in `scripts/Write-AtomicJson.ps1`
   - **Action:** Resolve and merge

3. **Roadmap alignment**
   - Regeneration logic needs cleanup
   - **Action:** Ensure single source of truth

### Clean State
- Git status: DIRTY (expected — docs being added)
- Encoding: BOM-free UTF-8✓
- Line endings: LF ✓
- Validation: scripts/validate-roadmap.ps1 available

## Standards
- **No direct push to main** — PR workflow only
- **Atomic writes** — use Write-AtomicJson.ps1
- **BOM-free UTF-8 + LF** — enforced
- **Validation required** — before every commit
- **Real-money resilience** — data integrity first

## File Structure

G:\s43_work\s43_g11_work\
├── .ai/
│   ├── init.ps1              # Context loader
│   └── verify-context.ps1    # AI self-test
├── docs/
│   ├── AI_ONBOARDING.md      # Agent onboarding
│   └── PHASE_B1_CHECKLIST.md # Next phase tasks
├── scripts/
│   ├── validate-roadmap.ps1  # Pre-commit check
│   └── Write-AtomicJson.ps1  # Safe JSON write
├── ROADMAP_CURRENT.json      # Source of truth
└── HANDOFF.md                # This file

## Next Steps for New Agent
1. Run `.ai/init.ps1` to load context
2. Read `docs/AI_ONBOARDING.md` for rules
3. Read `docs/PHASE_B1_CHECKLIST.md` for tasks
4. Run `.ai/verify-context.ps1` to self-test
5. Resolve Phase A blockers before touching Phase B1

## Key Contacts
- Repo: GitHub (9 required checks for PR merge)
- Tools: asoctl.py (primary control script)
- Language: Python, PowerShell