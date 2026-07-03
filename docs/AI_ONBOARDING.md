# AI Agent Onboarding — ASO-X

## Identity
- **Project:** ASO-X
- **Mission:** Global Financial Intelligence
- **Active Phase:** Phase A (governance) → Phase B1 (durability)
- **Repo:** immutable Git, PRs only, 9 checks

## Mental Model
You are operating on a **real-money financial system**.
Every decision must prioritize data integrity over convenience.

## Source of Truth
| Asset | Location |
|---|---|
| Roadmap | `ROADMAP_CURRENT.json` |
| Phase docs | `docs/` |
| Validation | `scripts/validate-roadmap.ps1` |

`source_of_truth` field in JSON **must equal** `repository_files_only`.

## Critical Rules
1. **Never push to `main` directly** — PR only
2. **Atomic write always** — use `Write-AtomicJson.ps1`
3. **BOM-free UTF-8 + LF** — no exceptions
4. **validate-roadmap.ps1 must pass** before any commit
5. **No parallel sources** — ROADMAP_CURRENT.json is authoritative

## File Encoding Check
```powershell
# Verify BOM-free
$b = [System.IO.File]::ReadAllBytes("ROADMAP_CURRENT.json")
if ($b[0] -eq 0xEF) { Write-Error "BOM detected!" }

## Onboarding Sequence
1. Run `.ai/init.ps1` — context snapshot
2. Read `HANDOFF.md` — current state
3. Read this file — rules
4. Read `docs/PHASE_B1_CHECKLIST.md` — next tasks
5. Run `.ai/verify-context.ps1` — self-test

## Phase A Blockers (resolve first)
- `source_of_truth` mismatch in ROADMAP_CURRENT.json
- PR #190 merge conflicts (scripts/Write-AtomicJson.ps1)
- Roadmap regeneration alignment

## Do NOT
- Edit ROADMAP_CURRENT.json without atomic write
- Skip validation before commit
- Add BOM to any file
- Use CRLF line endings
- Merge without PR review