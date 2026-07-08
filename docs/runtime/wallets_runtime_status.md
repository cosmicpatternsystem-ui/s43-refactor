# Wallets Runtime Status

## Current Mode

SAFE-NO-TRADE

## Wallet Slots

| Wallet | Slot | Token Env | Status |
|---|---:|---|---|
| Wallet 1 | 1 | ARZPLUS_TOKEN_1 | Prepared |
| Wallet 2 | 2 | ARZPLUS_TOKEN_2 | Prepared |
| Wallet 3 | 3 | ARZPLUS_TOKEN_3 | Prepared |

## Generic Fallback

ARZPLUS_TOKEN should be unset during isolated three-wallet runtime.

Reason:
- Prevent accidental sharing of one fallback token across all wallets.
- Keep wallet isolation clear.

## Current Exchange Issue

HTTP 403 {"detail":"توکن نامعتبر"} is treated as Arzplus exchange-side temporary issue.

## Safety

No live trading.
No buy.
No sell.
No order placement.
No auth/base_url/endpoint changes.
