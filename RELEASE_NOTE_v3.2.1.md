# v3.2.1

Title: feat(evidence): add ledger verify modes and align contract
Date (UTC): 2026-07-10 04:04:43Z
Branch: main
Verified HEAD before release commit: 981b1d09

## Repair
- Recorded a new evidence ledger entry for the updated contract-aligned example artifact.
- Preserved historical ledger entries without destructive rewrite.

## Verification
- python .\asoctl.py evidence ledger-record --record-path .\artifacts\examples\evidence_record.example.json --ledger-dir .\artifacts\evidence\ledger
- python .\asoctl.py evidence ledger-verify
- python .\asoctl.py evidence ledger-verify --latest-only
- python .\asoctl.py evidence ledger-verify --jsonl-audit
- python .\asoctl.py evidence ledger-verify --strict-history
- python .\repo\tools\validate_evidence_record.py .\artifacts\examples\evidence_record.example.json
- python -c "import json; json.load(open(r'.\repo\schemas\evidence_record.schema.json', encoding='utf-8')); print('SCHEMA_JSON_OK')"

## Result
- Evidence ledger is aligned with current evidence artifact state.
- Release tag is created only after successful verification and commit.