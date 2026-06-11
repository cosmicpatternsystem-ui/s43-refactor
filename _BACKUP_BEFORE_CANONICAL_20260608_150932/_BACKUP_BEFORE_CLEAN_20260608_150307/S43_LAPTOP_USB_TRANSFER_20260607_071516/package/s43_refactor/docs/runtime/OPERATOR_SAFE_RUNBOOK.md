# Operator Safe Runbook

## Purpose

This runbook defines the safe operational procedure for the current repository state.

The repository is currently in SAFE-NO-TRADE mode because Arzplus HTTP 403 is still treated as an exchange-side temporary issue.

This document is for safe monitoring and controlled validation only.

## Current Safety State

Current assumptions:

- Runtime is stable
- Bot compiles successfully
- Live trading must remain disabled
- Buy/sell/order placement must not be enabled
- HTTP 403 is treated as a temporary external issue
- Cooldown behavior is expected and acceptable
- No auth mutation is authorized
- No endpoint/base_url mutation is authorized

## Wallet Slot Mapping

Wallet slot mapping is fixed as:

- Wallet 1 -> slot 1 -> ARZPLUS_TOKEN_1
- Wallet 2 -> slot 2 -> ARZPLUS_TOKEN_2
- Wallet 3 -> slot 3 -> ARZPLUS_TOKEN_3

Supported runtime controls already include:

- CLI argument: --wallets
- default BotConfig slots: [1, 2, 3]
- per-slot token resolver: get_arzplus_token(slot)

## Required Token Setup

Recommended environment configuration:

export ARZPLUS_TOKEN_1='real_wallet_1_token'
export ARZPLUS_TOKEN_2='real_wallet_2_token'
export ARZPLUS_TOKEN_3='real_wallet_3_token'
unset ARZPLUS_TOKEN

Reason:

- ARZPLUS_TOKEN is only a generic fallback
- production-style multi-wallet isolation should use slot-specific tokens
- generic fallback should not be relied on for three-wallet operation

## Explicit Prohibitions

Do not change:

- authorization scheme
- token logic
- bearer/token style
- base_url
- endpoints
- exchange auth behavior

Do not enable:

- live trading
- buy path
- sell path
- order placement
- market order
- limit order

## Safe Runtime Commands

Single-wallet safe check:

python s43.py --wallets 1

Three-wallet safe check:

python s43.py --wallets 1,2,3

If current CLI parsing expects space-separated values, use:

python s43.py --wallets 1 2 3

Use only the form already accepted by the current implementation.

## Expected Behavior During HTTP 403

If Arzplus still returns HTTP 403, expected behavior includes:

- balance call may fail with HTTP 403
- bot logs ISOCHK_GLOBAL
- bot enters ISOCHK_GLOBAL_COOLDOWN
- bot does not crash
- bot does not place orders
- bot remains SAFE-NO-TRADE

This is currently considered acceptable safe behavior.

## Pre-Run Safety Checklist

Before running any safe check:

1. confirm correct branch
2. confirm no unintended local code edits
3. confirm slot-specific tokens are exported
4. confirm ARZPLUS_TOKEN generic fallback is unset
5. confirm no live trading change has been introduced
6. confirm goal is monitoring/validation only

## Post-Recovery Validation Checklist

Only after Arzplus recovers from HTTP 403:

1. compile check

python -m py_compile s43.py && echo COMPILE_OK

2. wallet 1 safe check

timeout 90s python s43.py --wallets 1 2>&1 | tee post_recovery_wallet1.log

3. wallet 2 safe check

timeout 90s python s43.py --wallets 2 2>&1 | tee post_recovery_wallet2.log

4. wallet 3 safe check

timeout 90s python s43.py --wallets 3 2>&1 | tee post_recovery_wallet3.log

5. all-wallet safe check

timeout 90s python s43.py --wallets 1,2,3 2>&1 | tee post_recovery_all_wallets.log

6. confirm:

- NO_RUNTIME_CRASH_FOUND
- NO_403_FOUND
- no unexpected auth mutation
- no order placement
- no unsafe runtime progression

## Incident Rule

If runtime behavior differs from expected SAFE-NO-TRADE behavior:

- stop
- do not enable workarounds blindly
- do not change auth experimentally
- do not change endpoints experimentally
- do not enable trading for diagnosis
- capture logs safely
- review against hardening docs and tests first

## References

- docs/roadmap/PHASE8_ROADMAP.md
- docs/roadmap/PHASE7_HARDENING_INDEX.md
- THREE_WALLETS_RUNTIME_PLAN.md
- PHASE7C_NODATA_USDTPX_GUARD_STATUS.md
- PHASE6_TEST_ORCHESTRATION_STATUS.md
