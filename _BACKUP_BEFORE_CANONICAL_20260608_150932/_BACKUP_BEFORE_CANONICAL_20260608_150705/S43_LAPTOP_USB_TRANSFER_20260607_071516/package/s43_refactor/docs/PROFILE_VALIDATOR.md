# Profile Validator

## Purpose

tools/validate_wallet_profiles.py is a read-only validation tool for the
TriWallet profile layer.

It validates wallet profile JSON files without modifying runtime behavior and
without importing s43.py.

## Scope

This tool checks:

- top-level schema shape
- required keys
- unknown keys
- wallet object structure
- default profile consistency
- basic value typing

## Usage

python tools/validate_wallet_profiles.py config/wallet_profiles.example.json

Optional JSON report output:

python tools/validate_wallet_profiles.py config/wallet_profiles.example.json --report-json .patch_audit/profile_validator_report.json

## Guarantees

- read-only validation
- no runtime patching
- no import from s43.py
- safe for configuration audit workflows
