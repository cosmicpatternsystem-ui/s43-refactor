# Release Note: Evidence Contract Alignment

Date: 2026-07-14

## Release Type

Refactor and contract hardening

## Summary

This phase completes live Evidence contract alignment by standardizing canonical field names across runtime code, tests, scripts, and active artifacts.

Canonical terminology:
- `event_type`
- `payload_hash`

Removed live legacy terminology:
- `evidence_type`
- `content_hash`

## Included Changes

- aligned Evidence runtime and supporting scripts to canonical field names
- aligned Evidence tests to canonical field names
- aligned live evidence artifacts to canonical field names
- corrected UTF-8 BOM regression in touched JSON artifacts
- added repository guard coverage to detect future contract regression

## Validation

- focused Evidence tests passed
- full Evidence suite passed
- residual live legacy scan passed
- governance pre-commit validation passed

## Exclusions

Historical audit snapshots under `artifacts/audits/` remain unchanged to preserve historical integrity and audit immutability.

## Primary Commits

- `7c60fda` `refactor(evidence): align records with canonical schema`
- `87456e5` `refactor(evidence): final contract alignment and path verification`
- `651ca24` `refactor(evidence): deep align live artifacts and roadmap hash contract`

## Operational Result

The active Evidence surface is now canonical and zero-legacy within live scope.