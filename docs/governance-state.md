# Governance State

Generated at: 2026-07-11T06:45:59Z

## Durable Facts
- Current branch: docs/governance-state-f14321d
- Target branch: main
- HEAD: 40d7f5b (40d7f5ba9a564953bc020e591c4dc87d45c79d95)
- Working tree clean before persist step: True
- Remote origin: git@github.com:cosmicpatternsystem-ui/s43-refactor.git

## Verification
- Syntax check: python -c "import ast, pathlib; ast.parse(pathlib.Path('asoctl.py').read_text(encoding='utf-8-sig')); print('syntax: ok')"
- Governance validation: python .\asoctl.py validate

## ASO Control
- File: soctl.py
- governance_validate definition count in ASOControl: 1

## Artifacts
- Manifest present: True
- Audit CSV present: True
- Ledger present: True
- Log present: True
- Evidence directory present: True
- Persisted state JSON present: True
- Persisted validation log present: True

## Source of Truth
This file is generated from repository state, git metadata, and command output.
It does not rely on chat memory.