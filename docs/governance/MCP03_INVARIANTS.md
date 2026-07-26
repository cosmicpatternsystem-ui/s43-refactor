# MCP-03 Invariants

Version: 1.0.0
Status: FORMALIZED
Phase: 32.01 — Operational Intelligence Runtime Governance
Authority: MCP-03 Compliance (Immutable Git + Formal Audit)
Source: jadid12.pdf (p.1 L5; p.2 L12-13)

## INV-MCP03-000 — Roadmap Atomicity (MANDATORY, per MCP-03)
**Statement:** All roadmap updates MUST be atomic across MD, JSON, and phase structure.
Any commit touching `docs/governance/ROADMAP_CANONICAL.md` MUST also update
`docs/governance/ROADMAP_CURRENT.json` in the same commit, and vice versa.
**Enforcement:** MUST
**CI Gate:** `python scripts/validate_mcp03_invariants.py --inv INV-MCP03-000`

## INV-MCP03-001 — Resolver Determinism
**Statement:** For identical input state, `scripts/resolve_next_action.py` MUST produce identical output.
**Enforcement:** MUST
**CI Gate:** `python scripts/validate_mcp03_invariants.py --inv INV-MCP03-001`

## INV-MCP03-002 — Ledger Immutability
**Statement:** Committed ledger entries MUST NOT be modified or deleted (Immutable Git).
**Enforcement:** MUST
**CI Gate:** `python scripts/validate_mcp03_invariants.py --inv INV-MCP03-002`

## INV-MCP03-003 — Roadmap Authority
**Statement:** `ROADMAP_CANONICAL.md` is the sole source of truth; `ROADMAP_CURRENT.json` MUST be a derived, valid artifact.
**Enforcement:** MUST
**CI Gate:** `python scripts/validate_mcp03_invariants.py --inv INV-MCP03-003`

## INV-MCP03-004 — UTF-8/LF Encoding
**Statement:** All governance documents MUST be UTF-8 without BOM, LF line endings.
**Enforcement:** MUST
**CI Gate:** `python scripts/validate_mcp03_invariants.py --inv INV-MCP03-004`

## INV-MCP03-005 — CI Gate Non-Bypass
**Statement:** No merge to `main` is permitted with a failing CI gate (Formal Audit).
**Enforcement:** MUST
**CI Gate:** `.github/scripts/governance-guard.ps1`

<!-- MCP03-DOC-ONLY-WAIVER v1 -->
## Documentation-Only Evidence Waiver

- Status: ACTIVE
- Scope: phases where documentation_only == true AND status == "complete" AND evidence == []
- Count at issuance: 27 phases
- Expiry: 2026-08-01T00:00:00Z
- Enforcement: gate logs each pass as GATE_WAIVED (no silent pass); after Expiry the same phases become GATE_FAIL and trigger Budget Freeze.
- Renewal: requires explicit review plus update of this clause and the gate constant.
