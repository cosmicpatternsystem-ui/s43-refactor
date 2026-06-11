# Three Wallets Runtime Plan

## Purpose

Prepare stable management for three Arzplus wallets while the exchange-side HTTP 403 issue is still active.

Current status:
- Bot compiles successfully.
- Runtime is stable.
- Bot remains SAFE-NO-TRADE.
- Cooldown is active.
- HTTP 403 is treated as a temporary Arzplus exchange-side issue.

## Wallet Slot Mapping

Wallet slot mapping is fixed as:

- Wallet 1 -> slot 1 -> ARZPLUS_TOKEN_1
- Wallet 2 -> slot 2 -> ARZPLUS_TOKEN_2
- Wallet 3 -> slot 3 -> ARZPLUS_TOKEN_3

The bot already supports wallet slots through:

- CLI argument: --wallets
- Default slots in BotConfig: [1, 2, 3]
- Per-slot token resolver: get_arzplus_token(slot)

## Important Rules

Do not change:
- Authorization scheme
- Token/Bearer logic
- base_url
- endpoint
- auth logic
- exchange client auth behavior

Do not enable:
- live trading
- buy path
- sell path
- order placement
- market order
- limit order

## Token Safety

Each wallet should use its own dedicated token.

Recommended runtime environment:

export ARZPLUS_TOKEN_1='real_wallet_1_token'
export ARZPLUS_TOKEN_2='real_wallet_2_token'
export ARZPLUS_TOKEN_3='real_wallet_3_token'
unset ARZPLUS_TOKEN

Reason:
- ARZPLUS_TOKEN is a generic fallback.
- For three-wallet isolation, each slot should have its own slot-specific token.
- Generic fallback should not be used for production multi-wallet runtime.

## Current Exchange Status

HTTP 403 {"detail":"توکن نامعتبر"} is currently treated as a temporary Arzplus exchange-side issue.

Until Arzplus recovery:
- Only run safe monitoring.
- Do not change auth.
- Do not change endpoint.
- Do not try Bearer instead of Token.
- Do not activate live trading.

## Safe Runtime Modes

Single-wallet safe check:

python s43.py --wallets 1

Three-wallet safe check after token setup:

python s43.py --wallets 1,2,3

If CLI parsing expects space-separated wallet args, use:

python s43.py --wallets 1 2 3

Use whichever form is already accepted by current s43.py.

## Expected Behavior During 403

Expected:
- First get_balance may return HTTP 403.
- Bot logs ISOCHK_GLOBAL.
- Bot enters ISOCHK_GLOBAL_COOLDOWN.
- Bot does not crash.
- Bot does not place orders.
- Bot remains SAFE-NO-TRADE.

## Post-Recovery Checklist

After Arzplus recovery:

1. Compile:
   python -m py_compile s43.py && echo COMPILE_OK

2. Test wallet 1:
   timeout 90s python s43.py --wallets 1 2>&1 | tee post_recovery_wallet1.log

3. Test wallet 2:
   timeout 90s python s43.py --wallets 2 2>&1 | tee post_recovery_wallet2.log

4. Test wallet 3:
   timeout 90s python s43.py --wallets 3 2>&1 | tee post_recovery_wallet3.log

5. Test all wallets:
   timeout 90s python s43.py --wallets 1,2,3 2>&1 | tee post_recovery_all_wallets.log

6. Confirm:
   - NO_RUNTIME_CRASH_FOUND
   - NO_403_FOUND
   - NO_TRADE_ACTION_FOUND
   - balance parsing works
   - cooldown behavior remains safe

## Final Rule

Three-wallet runtime may be prepared now, but live trading must remain disabled until an explicit final decision.
