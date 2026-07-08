# ASO-X CONSTITUTION v0.1

## 1. PURPOSE
ASO-X is a global financial intelligence infrastructure built for 50-year durability, policy-driven governance, and machine-verifiable evidence.

## 2. CORE PRINCIPLES
- **Evidence over Assumption**: No state change without a signed ledger entry.
- **Policy over Improvisation**: All actions must derive from an explicit policy file.
- **Canonical Source of Truth**: The Repository is the ONLY source of truth. Chat memory is non-binding.
- **Fail Closed**: In case of ambiguity or evidence mismatch, the system must halt/block.

## 3. AUTHORITY HIERARCHY
1. CONSTITUTION.md (This Document)
2. ROADMAP_CANONICAL.md
3. *.policy.json files
4. asoctl.py / Automation Logic
5. Generated Artifacts / Evidence

## 4. PERSISTENCE STANDARDS
- All records must be UTF-8 (LF).
- Evidence must be signed and archived.
- Real-money resilience is the baseline for all validation logic.
