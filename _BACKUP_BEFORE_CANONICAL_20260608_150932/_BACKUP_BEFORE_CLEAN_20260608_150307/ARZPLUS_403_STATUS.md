# Arzplus 403 Temporary Status

HTTP 403 {"detail":"توکن نامعتبر"} is currently treated as a temporary Arzplus exchange-side issue.

Bot status:
- COMPILE_OK
- Runtime stable
- SAFE-NO-TRADE
- Cooldown active
- No trade action detected

Do not change:
- Authorization scheme
- Token/Bearer logic
- base_url
- endpoint
- auth logic

Next action:
Wait for Arzplus recovery, then run post-recovery checklist.

## Quick Watch Check

Result:
- COMPILE_OK
- NO_RUNTIME_CRASH_FOUND
- NO_TRADE_ACTION_FOUND
- ISOCHK_GLOBAL_COOLDOWN active
- HTTP 403 still present from Arzplus side
- Bot remains SAFE-NO-TRADE

Conclusion:
Baseline health confirmed. No auth/base_url/endpoint changes required.
