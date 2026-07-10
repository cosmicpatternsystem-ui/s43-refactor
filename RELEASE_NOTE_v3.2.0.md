# v3.2.0

Title: feat(evidence): add ledger verify modes and align contract
Date (UTC): 2026-07-10 03:44:56Z
Branch: main
HEAD: 981b1d09

## Added
- Added evidence ledger-verify modes:
  - historical scan (default)
  - strict history validation
  - latest-only verification
  - JSONL audit output format

## Changed
- Aligned evidence contract with mandatory fields:
  - producer
  - subject
  - etention
- Synced JSON schema, structural validator, and example artifacts with contract updates

## Verification Performed
- Checked default ledger validation
- Performed strict history verification (logged)
- Executed latest-only target verification
- Audited JSONL stream compliance
- Executed semantic validator against schema
- Verified UTF-8 compliance of schema definitions

## Result
- Main integration tests passed successfully
- Working tree clean
- Release artifact ready for distribution