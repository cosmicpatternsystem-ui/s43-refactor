from pathlib import Path

p = Path("s43.py")
src = p.read_text(encoding="utf-8")

old1 = '''        except Exception as e:
            try:
                _fc = int(getattr(self, "_balance_fail_count", 0) or 0) + 1
                setattr(self, "_balance_fail_count", _fc)
                setattr(self, "_balance_disabled_until", time.time() + 120.0)
                print(f"ISOCHK phase=portfolio_data err={type(e).__name__}:{e} fail_count={_fc}", flush=True)
            except Exception:
                pass
            raise TradingHalt("BALANCE_FETCH_FAILED: DASH_PORTFOLIO_BALANCE") from e
'''
new1 = '''        except Exception as e:
            try:
                _fc = int(getattr(self, "_balance_fail_count", 0) or 0) + 1
                setattr(self, "_balance_fail_count", _fc)
                setattr(self, "_balance_disabled_until", time.time() + 120.0)
                print(f"ISOCHK phase=portfolio_data err={type(e).__name__}:{e} fail_count={_fc}", flush=True)
            except Exception:
                pass
            try:
                logging.warning(
                    "ISOCHK_GLOBAL phase=portfolio_data err=%s",
                    f"{type(e).__name__}: {e}",
                )
            except Exception:
                pass
            return {
                "capital": 0.0,
                "exposure": 0.0,
                "positions": []
            }
'''

if old1 not in src:
    raise SystemExit("PATCH13_3_FAIL: block old1 not found")
src = src.replace(old1, new1, 1)

anchor = '''    async def _refresh_wallet_balance(self, w) -> float:
'''
if anchor not in src:
    raise SystemExit("PATCH13_3_FAIL: refresh anchor not found")

old2 = '''    async def _refresh_wallet_balance(self, w) -> float:
        now = time.time()
'''
new2 = '''    async def _refresh_wallet_balance(self, w) -> float:
        now = time.time()
        def _balance_refresh_degraded(reason: str) -> float:
            try:
                w.last_balance_ok = False
            except Exception:
                pass
            try:
                w.last_balance_ts = now
            except Exception:
                pass
            try:
                w.last_balance_err = str(reason)[:300]
            except Exception:
                pass
            return float(getattr(w, "cash_irt", 0.0) or 0.0)
'''
if old2 not in src:
    raise SystemExit("PATCH13_3_FAIL: block old2 not found")
src = src.replace(old2, new2, 1)

repls = [
    (
        '''            raise TradingHalt(f"BALANCE_FETCH_FAILED: TRANSIENT: {type(e).__name__}:{e}") from e''',
        '''            return _balance_refresh_degraded(f"BALANCE_FETCH_FAILED: TRANSIENT: {type(e).__name__}:{e}")'''
    ),
    (
        '''            raise TradingHalt(f"BALANCE_FETCH_FAILED: HTTP_FAIL: {type(e).__name__}:{e}") from e''',
        '''            return _balance_refresh_degraded(f"BALANCE_FETCH_FAILED: HTTP_FAIL: {type(e).__name__}:{e}")'''
    ),
    (
        '''                  raise TradingHalt(f"BALANCE_FETCH_FAILED: TRANSIENT: {type(e).__name__}:{e}") from e''',
        '''                  return _balance_refresh_degraded(f"BALANCE_FETCH_FAILED: TRANSIENT: {type(e).__name__}:{e}")'''
    ),
    (
        '''              raise TradingHalt(f"BALANCE_FETCH_FAILED: API_FAIL: {type(e).__name__}:{e}") from e''',
        '''              return _balance_refresh_degraded(f"BALANCE_FETCH_FAILED: API_FAIL: {type(e).__name__}:{e}")'''
    ),
    (
        '''              raise TradingHalt("BALANCE_FETCH_FAILED: EXC") from e''',
        '''              return _balance_refresh_degraded("BALANCE_FETCH_FAILED: EXC")'''
    ),
    (
        '''              raise TradingHalt("BALANCE_FETCH_FAILED: ARZPLUS_FAST_PARSE_FAIL") from e''',
        '''              return _balance_refresh_degraded("BALANCE_FETCH_FAILED: ARZPLUS_FAST_PARSE_FAIL")'''
    ),
    (
        '''          else: raise TradingHalt("BALANCE_FETCH_FAILED: PARSE_OK_FALSE")''',
        '''          else: return _balance_refresh_degraded("BALANCE_FETCH_FAILED: PARSE_OK_FALSE")'''
    ),
]

for old, new in repls:
    if old not in src:
        raise SystemExit(f"PATCH13_3_FAIL: replacement target not found:\n{old}")
    src = src.replace(old, new, 1)

p.write_text(src, encoding="utf-8")
print("PATCH13_3_OK")
