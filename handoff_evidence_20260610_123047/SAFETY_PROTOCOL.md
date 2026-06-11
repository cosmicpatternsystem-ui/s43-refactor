# S43 Safety Protocol

## Purpose

This document defines the current operational safety model of the S43 trading bot based on the existing implementation.

It documents safety gates, autonomous trading controls, AI execution guards, and risk-layer behavior without modifying Python source code.

## Current Safety Baseline

- `MY_S43_LATEST.py` and `s43.py` are identical.
- Python source code is not modified by this document.
- This document is informational and operational.

---

## 1. Autonomous AI Gate

The primary autonomous behavior gate is controlled by:

~~~python
AUTONOMOUS_AI
~~~

Implementation reference:

~~~python
autonomous_ai: bool = field(default_factory=lambda: _env_bool("AUTONOMOUS_AI", False))
~~~

Source:

- `MY_S43_LATEST.py`, line `323`

### Safety Meaning

`AUTONOMOUS_AI` is default-off.

Production deployments must treat `AUTONOMOUS_AI=False` as the safe default.

---

## 2. AI Trade Execution Gate

The AI trade execution path is protected by a multi-condition gate.

Implementation reference:

~~~python
if getattr(self, "_ai_trader", None) is not None and bool(getattr(w.cfg, "autonomous_ai", False)) and bool(_env_bool("OPENAI_TRADE_ENABLE", False)) and bool(_env_bool("OPENAI_TRADE_ALLOW_ND", False)):
~~~

Source:

- `MY_S43_LATEST.py`, lines `20003-20060`

AI-driven trade execution requires all of the following:

1. `_ai_trader` must exist.
2. Wallet/config-level `autonomous_ai` must be enabled.
3. `OPENAI_TRADE_ENABLE` must be enabled.
4. `OPENAI_TRADE_ALLOW_ND` must be enabled.

Failure of any condition prevents the AI trading path from activating.

---

## 3. Risk Decision Layer

The `RiskDecision` class is used as part of the risk-control layer.

Source:

- `MY_S43_LATEST.py`, line `5807`

Known decision fields include:

- `allow_entries`
- `allow_exits`

The risk layer can affect whether the system is allowed to enter or exit trades.

---

## 4. Order Placement Path

The function name `place_order` appears as a real order execution candidate.

Known references:

- `MY_S43_LATEST.py`, line `3230`
- `MY_S43_LATEST.py`, line `15057`

`place_order` should be treated as a critical execution boundary.

Future code modification around `place_order` must be reviewed as high-risk.

---

## 5. Emergency Stop / Kill Switch Status

No explicit classic kill switch names were found in the current codebase, including:

~~~text
kill_switch
emergency_stop
stop_trading
trading_disabled
disable_trading
~~~

The code appears to implement safe-state behavior through distributed mechanisms:

- `_ai_live_trading_armed`
- `RISK_W_NET_PAUSE`
- `PhoenixDecision`
- `FLAT` state handling

Sources:

- `MY_S43_LATEST.py`, line `5829`
- `MY_S43_LATEST.py`, line `7241`

Recommended future central switch names:

~~~text
TRADING_GLOBAL_KILL_SWITCH
S43_EMERGENCY_STOP
~~~

---

## 6. Missing Marker: READY_FOR_AUTONOMOUS_DECISION

The marker below was not found in the current codebase:

~~~text
READY_FOR_AUTONOMOUS_DECISION
~~~

There is no explicit final readiness marker for autonomous decision execution.

---

## 7. Current Safety Interpretation

~~~text
AI trading execution =
    _ai_trader exists
    AND autonomous_ai enabled
    AND OPENAI_TRADE_ENABLE enabled
    AND OPENAI_TRADE_ALLOW_ND enabled
    AND risk/order layers allow execution
~~~

If any required layer fails, AI-driven trade execution should not proceed.

---

## 8. Review Requirements for Future Changes

Any future change touching the following areas must be treated as high-risk:

- `place_order`
- `_ai_trader`
- `AUTONOMOUS_AI`
- `OPENAI_TRADE_ENABLE`
- `OPENAI_TRADE_ALLOW_ND`
- `RiskDecision`
- `PhoenixDecision`
- wallet execution configuration
- live trading flags

Required review steps:

1. Update this document.
2. Run baseline hash verification.
3. Run `py_compile`.
4. Review diff manually.
5. Confirm default-off behavior remains unchanged.
6. Confirm no execution path bypasses risk gates.

---

## Status

~~~text
SAFETY DOCUMENTATION ONLY - NO CODE CHANGE
~~~
