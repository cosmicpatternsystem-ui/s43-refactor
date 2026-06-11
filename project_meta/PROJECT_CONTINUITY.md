# PROJECT_CONTINUITY.md

Project: S43 Safety-Gated Refactor and Canonical Selection
Date: 2026-06-09
Status: Active Continuity Record

## Purpose

This file is the official continuity record for new sessions.

The project must continue from the approved three-file working model.

## Official Three-File Working Model

### 1. Baseline / Original Main

File: MY_S43_LATEST.py

Role:
- Official baseline
- Source of Truth
- Reference for behavior comparison
- Parity validation reference

Rules:
- Do not modify directly.
- Use only for reading, comparison, and baseline extraction.
- Treat as the risk-control reference.

### 2. Sandbox / Main Copy

File: s43_latest_refactor.py

Role:
- Safe working copy
- Sandbox for structural refactor
- Place for uncertain changes and intermediate patching

Rules:
- Use for experiments and refactor work.
- Do not treat as canonical unless explicitly validated later.
- Promote logic only after review.

### 3. Final Candidate / Instrumented Validation Track

File: s43_instrumented_LATEST.py

Role:
- Primary final candidate
- Instrumented validation target
- Safety-gate visibility target
- API validation and parity-check target

Rules:
- Use for validation and final-candidate evaluation.
- Keep safety-gate logging visible.
- Do not declare canonical before parity validation.

## Governing Reference Documents

Reference files:
- SAFETY_PROTOCOL.md
- SAFETY_GATE_MAPPING_PASS1.txt
- SAFETY_PROTOCOL_FINAL_VERIFY_20260608_175301.txt

These documents govern:
- three-tier model
- checkpoint discipline
- safety-gate visibility
- parity-before-canonical-selection rule
- rework avoidance

## Official Interpretation Rules

Use this mapping in every new session:

- MY_S43_LATEST.py = Baseline
- s43_latest_refactor.py = Sandbox
- s43_instrumented_LATEST.py = Primary Final Candidate

No other file should replace these roles unless an explicit decision is made after parity validation.

## Mandatory Working Rules

1. Do not directly modify MY_S43_LATEST.py.
2. Use s43_latest_refactor.py for uncertain or structural changes.
3. Use s43_instrumented_LATEST.py for validation and final-candidate evaluation.
4. Do not declare a canonical main before parity validation.
5. Prioritize baseline evidence, safety protocol requirements, parity evidence, and API correctness.

## Known Technical Focus Areas

1. base_url
   Required target: https://api.arzplus.net

2. Authorization header format
   Verify Bearer vs Token.

3. Endpoint versioning
   Verify v1 vs v2.

4. Wallet balance path
   Investigate wallet/balance 403 behavior.

5. Safety-gate visibility
   Confirm logging and checkpoint traceability.

6. Live execution parity
   Compare baseline behavior with the instrumented candidate.

## Official Phase Model

Phase 0: Baseline Lock
Target: MY_S43_LATEST.py
Status: Completed

Phase 1: Sandbox Refactor
Target: s43_latest_refactor.py
Status: Active

Phase 2: Instrumented Validation
Target: s43_instrumented_LATEST.py
Status: Active

Phase 3: Parity Validation
Compare:
- MY_S43_LATEST.py
- s43_instrumented_LATEST.py
Status: Pending

Phase 4: Canonical Selection
Status: Not allowed yet

## Immediate Next Step

Run parity validation between:
- MY_S43_LATEST.py
- s43_instrumented_LATEST.py

Validate:
- base_url
- Authorization format
- endpoint versioning
- wallet/balance flow
- safety-gate logging
- live execution path
- error handling behavior

## Canonical Selection Rule

No file may be declared canonical before:
- parity validation is completed
- safety-gate behavior is reviewed
- API compatibility is confirmed
- differences from baseline are documented and accepted

## Official Status Summary

Baseline: MY_S43_LATEST.py
Sandbox: s43_latest_refactor.py
Final Candidate: s43_instrumented_LATEST.py
Canonical Main: Not selected yet
Required Next Action: Parity validation