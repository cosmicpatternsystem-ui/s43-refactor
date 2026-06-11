# S43 Consolidated Roadmap

## Current Source Layout

Canonical editable baseline:
- MY_S43_LATEST.py

Runtime entry point:
- s43.py

Candidate/reference version:
- s43_instrumented_LATEST.py

Companion documentation:
- AI_REFACTOR_CONTEXT.md
- AI_NEXT_STEPS.md
- AI_SAFETY_GUARDS.md
- AI_DIFF_NOTES.md
- ROADMAP_CONSOLIDATED.md

Non-source material:
- pasted-text.txt is terminal/log/paste material only.
- pasted-text.txt must not be used as source code.

## Current Known State

- MY_S43_LATEST.py and s43.py are the baseline pair.
- s43.py should be treated as the runtime copy.
- MY_S43_LATEST.py should be edited first.
- s43.py should only be refreshed from MY_S43_LATEST.py after validation.
- s43_instrumented_LATEST.py is different and must remain as a candidate/reference until diff review is complete.
- Python syntax has previously compiled successfully for the main files.
- Repeated separator lines in the Python files are normal comments, not junk.

## Safety Position

Autonomous/live trading must remain disabled.

Required safe defaults:
- AUTONOMOUS_AI=0
- OPENAI_TRADE_ENABLE=0

Important rule:
- READY_FOR_AUTONOMOUS_DECISION is not permission for live autonomous trading.

Review before any activation:
- RiskDecision.assess
- PhoenixDecision
- AITrader
- _ai_trader
- AUTONOMOUS_AI checks
- OPENAI_TRADE_ENABLE checks
- wallet-level autonomous flags
- final trade execution path

## Main Roadmap

Phase 1: Freeze the baseline
- Keep MY_S43_LATEST.py as canonical.
- Keep s43.py as runtime copy.
- Keep s43_instrumented_LATEST.py as candidate/reference.
- Do not delete or overwrite candidate files.

Phase 2: Verify current integrity
- Confirm required files exist.
- Confirm MY_S43_LATEST.py and s43.py hashes match.
- Confirm all main Python files pass py_compile.
- Confirm companion docs exist.

Phase 3: Diff baseline vs candidate
- Compare MY_S43_LATEST.py with s43_instrumented_LATEST.py.
- Classify every meaningful change.
- Categories:
  - safe logging/instrumentation
  - comments/docs only
  - formatting only
  - config/env behavior
  - risk decision behavior
  - trade execution behavior
  - autonomous/live trading behavior
  - unknown/risky

Phase 4: Port only safe changes
- Apply only understood and safe changes into MY_S43_LATEST.py.
- Do not merge unknown trade/risk/autonomous behavior.
- Keep AUTONOMOUS_AI and OPENAI_TRADE_ENABLE disabled.
- Do not edit s43.py as primary source.

Phase 5: Validate
- Run py_compile after each meaningful change.
- Re-check key guards and decision paths.
- Compare MY_S43_LATEST.py and s43.py only after validation.
- Copy MY_S43_LATEST.py to s43.py only when validated.

Phase 6: Testing
- Add safe non-live tests where possible.
- Prioritize tests around:
  - RiskDecision.assess
  - market status note generation
  - PhoenixDecision
  - AI trader enable/disable behavior
  - final trade execution guard behavior

## Explicit Do Not Do

- Do not enable autonomous trading.
- Do not enable live OpenAI trade execution.
- Do not treat READY_FOR_AUTONOMOUS_DECISION as live permission.
- Do not use pasted-text.txt as code.
- Do not delete s43_instrumented_LATEST.py before diff review.
- Do not overwrite s43.py manually before validation.
- Do not merge candidate changes blindly.

## Next Immediate Action

Run a structured diff between:
- MY_S43_LATEST.py
- s43_instrumented_LATEST.py

Then produce a classification report before any code merge.