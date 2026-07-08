# Phase7C NO_DATA:USDT_PX Guard Status

## Commit

- Commit: cb191fc
- Tag: phase7c-consumer-nodata-usdtpx-guard
- Branch: hardening/phase7c-nodata-usdtpx-guard

## Test

- File: test_phase7c_consumer_nodata_usdtpx_guard.py
- Test:
  - test_consumer_nodata_usdtpx_sets_hold_rejects_and_returns_before_entry_multiplier

## Contract validated

- USDT-quoted symbol activates the USDT price wait path.
- Missing/invalid USDTIRT price triggers NO_DATA:USDT_PX.
- Engine state becomes Hold / NO_DATA:USDT_PX.
- Flow returns before entry_multiplier.
- Reject telemetry is validated.
- Test does not rely on brittle warning-log assertions.

## Last known result

python -m unittest -v test_phase7c_consumer_nodata_usdtpx_guard.py

Result:

Ran 1 test
OK
