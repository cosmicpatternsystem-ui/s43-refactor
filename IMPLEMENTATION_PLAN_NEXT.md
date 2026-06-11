# S43 Next Implementation Plan

## Purpose

This file converts the roadmap into immediate low-risk execution steps.
It is intentionally practical, short, and focused on the next implementation sessions.

## Current Ground Truth

Canonical editable source:
- MY_S43_LATEST.py

Runtime copy:
- s43.py

Candidate reference:
- s43_instrumented_LATEST.py

Core roadmap:
- ROADMAP_CONSOLIDATED.md

Supporting documents:
- AI_REFACTOR_CONTEXT.md
- AI_NEXT_STEPS.md
- AI_SAFETY_GUARDS.md
- AI_DIFF_NOTES.md

Known rules:
- Do not use pasted-text.txt as source code.
- Do not overwrite s43.py before validation.
- Do not delete or merge s43_instrumented_LATEST.py blindly.
- Keep AUTONOMOUS_AI disabled by default.
- Keep OPENAI_TRADE_ENABLE disabled by default.

## Session Priority Order

1. Preserve baseline integrity
2. Review candidate differences
3. Isolate configuration and safety controls
4. Prepare modular refactor with behavior preservation
5. Add validation steps before any autonomous or client-capital workflow

## Immediate Work Queue

### Step 1: Baseline verification
Goal:
- confirm the baseline files remain in the expected state

Tasks:
- verify MY_S43_LATEST.py exists
- verify s43.py exists
- verify s43_instrumented_LATEST.py exists
- verify ROADMAP_CONSOLIDATED.md exists
- run py_compile on all main Python files
- verify MY_S43_LATEST.py and s43.py still match if that is expected

Output:
- short status note
- updated AI_DIFF_NOTES.md only if baseline assumptions changed

### Step 2: Structured diff review
Goal:
- classify the candidate file before any merge decision

Tasks:
- compare MY_S43_LATEST.py with s43_instrumented_LATEST.py
- classify changes into:
  - safe refactor
  - logging/instrumentation
  - AI decision logic
  - risk logic
  - execution logic
  - config/env behavior
  - unknown behavior change
- record accepted/rejected/open items in AI_DIFF_NOTES.md

Output:
- a reviewed difference list
- no code merge yet unless fully understood

### Step 3: Safety gate mapping
Goal:
- identify exactly where autonomous and live execution are controlled

Tasks:
- locate AUTONOMOUS_AI checks
- locate OPENAI_TRADE_ENABLE checks
- locate READY_FOR_AUTONOMOUS_DECISION usage
- locate RiskDecision.assess
- locate PhoenixDecision
- locate _ai_trader and related decision path
- locate final execution guard
- identify where dry-run is enforced
- identify where kill-switch behavior should exist

Output:
- a short map of safety-critical functions and flags
- update AI_SAFETY_GUARDS.md if needed

### Step 4: Config extraction plan
Goal:
- reduce hard-coded behavior and prepare multi-platform deployment

Tasks:
- identify config values currently embedded in code
- group them into categories:
  - exchange
  - symbols
  - timeframes
  - wallet settings
  - AI settings
  - risk settings
  - runtime mode
  - logging paths
- propose a first config structure without changing behavior

Output:
- candidate config key list
- candidate profile split for future implementation

### Step 5: Refactor boundary definition
Goal:
- split future work into low-risk modules

Suggested target modules:
- config
- market data
- strategy
- risk
- AI decision
- execution
- accounting
- reporting
- platform

Tasks:
- identify which functions can move first with minimal behavior risk
- identify which code must stay untouched until later
- define a first extraction order

Output:
- small phased refactor order
- no broad rewrite

## Low-Risk Refactor Order

Recommended order:
1. constants and config access
2. logging helpers
3. utility helpers
4. non-trading reporting helpers
5. market-data helpers
6. risk helpers
7. AI decision wrappers
8. execution wrappers
9. accounting/client ledger modules

Avoid moving first:
- final order placement logic
- autonomous activation logic
- emergency stop behavior
- wallet-sensitive execution code
- payout logic before accounting design is defined

## Minimum Validation Per Session

Every coding session should end with:
- syntax validation
- quick import/launch smoke validation if possible
- confirmation that safety defaults remain unchanged
- confirmation that no unintended live behavior was enabled
- short note added to AI_DIFF_NOTES.md when meaningful changes occur

## Definition Of Done For The Next Phase

The next phase is complete when:
- candidate differences are classified
- safety-critical paths are mapped
- config extraction plan is written
- first refactor boundaries are defined
- baseline behavior is still preserved
- autonomous live execution is still disabled by default

## Explicit Do Not Do

- do not rewrite the whole file at once
- do not merge candidate code without classification
- do not enable autonomous trading
- do not enable OpenAI live execution
- do not add client-capital workflows before accounting design
- do not change runtime behavior and refactor structure in the same uncontrolled step
- do not rely on pasted-text.txt for source recovery

## Suggested Next Session Start

Start with:
1. file existence check
2. py_compile
3. hash or equality check for MY_S43_LATEST.py and s43.py
4. structured diff review against s43_instrumented_LATEST.py
5. write findings into AI_DIFF_NOTES.md