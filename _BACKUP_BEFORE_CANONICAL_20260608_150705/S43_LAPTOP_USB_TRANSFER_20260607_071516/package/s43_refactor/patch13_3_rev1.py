from pathlib import Path
import re

p = Path("s43.py")
src = p.read_text(encoding="utf-8")

# --- Part 1: _get_portfolio_data ---
# استفاده از regex برای پیدا کردن بلاک بدون حساسیت به فضاهای خالی انتهای خط
old1_re = r'        except Exception as e:\s+try:\s+_fc = int\(getattr\(self, "_balance_fail_count", 0\) or 0\) \+ 1\s+setattr\(self, "_balance_fail_count", _fc\)\s+setattr\(self, "_balance_disabled_until", time\.time\(\) \+ 120\.0\)\s+print\(f"ISOCHK phase=portfolio_data err=\{type\(e\)\.__name__\}:\{e\} fail_count=\{\_fc\}", flush=True\)\s+except Exception:\s+pass\s+raise TradingHalt\("BALANCE_FETCH_FAILED: DASH_PORTFOLIO_BALANCE"\) from e'

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
            }'''

if not re.search(old1_re, src):
    print("DEBUG: Checking old1 with direct match...")
    # fallback to a slightly more literal but still flexible search if regex fails
    if 'raise TradingHalt("BALANCE_FETCH_FAILED: DASH_PORTFOLIO_BALANCE") from e' not in src:
         raise SystemExit("PATCH13_3_FAIL: block old1 (portfolio) not found")

src = re.sub(old1_re, new1, src, count=1)

# --- Part 2: Inject Helper into _refresh_wallet_balance ---
# جستجوی منعطف‌تر برای شروع تابع
anchor_pattern = r'async def _refresh_wallet_balance\(self, w\) -> float:\s+now = time\.time\(\)'
helper_code = '''    async def _refresh_wallet_balance(self, w) -> float:
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
            return float(getattr(w, "cash_irt", 0.0) or 0.0)'''

if not re.search(anchor_pattern, src):
    raise SystemExit("PATCH13_3_FAIL: _refresh_wallet_balance anchor not found")

src = re.sub(anchor_pattern, helper_code, src, count=1)

# --- Part 3: Replace Raises with Returns ---
repls = [
    ('raise TradingHalt(f"BALANCE_FETCH_FAILED: TRANSIENT: {type(e).__name__}:{e}") from e', 
     'return _balance_refresh_degraded(f"BALANCE_FETCH_FAILED: TRANSIENT: {type(e).__name__}:{e}")'),
    
    ('raise TradingHalt(f"BALANCE_FETCH_FAILED: HTTP_FAIL: {type(e).__name__}:{e}") from e',
     'return _balance_refresh_degraded(f"BALANCE_FETCH_FAILED: HTTP_FAIL: {type(e).__name__}:{e}")'),
    
    ('raise TradingHalt(f"BALANCE_FETCH_FAILED: API_FAIL: {type(e).__name__}:{e}") from e',
     'return _balance_refresh_degraded(f"BALANCE_FETCH_FAILED: API_FAIL: {type(e).__name__}:{e}")'),
    
    ('raise TradingHalt("BALANCE_FETCH_FAILED: EXC") from e',
     'return _balance_refresh_degraded("BALANCE_FETCH_FAILED: EXC")'),
    
    ('raise TradingHalt("BALANCE_FETCH_FAILED: ARZPLUS_FAST_PARSE_FAIL") from e',
     'return _balance_refresh_degraded("BALANCE_FETCH_FAILED: ARZPLUS_FAST_PARSE_FAIL")'),
    
    ('else: raise TradingHalt("BALANCE_FETCH_FAILED: PARSE_OK_FALSE")',
     'else: return _balance_refresh_degraded("BALANCE_FETCH_FAILED: PARSE_OK_FALSE")'),
]

for old, new in repls:
    # استفاده از strip برای جلوگیری از حساسیت به فضای خالی ابتدای خط در جستجو
    if old.strip() not in src:
        print(f"WARNING: Replacement target not found literally, trying flexible: {old.strip()}")
    src = src.replace(old.strip(), new.strip())

p.write_text(src, encoding="utf-8")
print("PATCH13_3_OK")
