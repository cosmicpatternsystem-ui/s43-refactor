from pathlib import Path
from datetime import datetime

p = Path("s43.py")
src = p.read_text(encoding="utf-8")

marker = "# S43 PATCH B2 RUNTIME TOKEN METADATA INJECT"

if marker in src:
    print("INFO: runtime metadata inject already present")
    raise SystemExit(0)

needle = "self.wallets[wname] = wr"

idx = src.find(needle)
if idx < 0:
    raise SystemExit("ERROR: could not find target line: self.wallets[wname] = wr")

line_start = src.rfind("\n", 0, idx) + 1
indent = src[line_start:idx]
insert_pos = src.find("\n", idx)
if insert_pos < 0:
    insert_pos = len(src)
else:
    insert_pos += 1

block = f"""{indent}# {marker}
{indent}try:
{indent}    import os as _s43_b2_os
{indent}    import time as _s43_b2_time
{indent}    from datetime import datetime as _s43_b2_datetime, timezone as _s43_b2_timezone
{indent}
{indent}    def _s43_b2_first_env(*names):
{indent}        for _n in names:
{indent}            _v = _s43_b2_os.environ.get(_n)
{indent}            if _v is not None and str(_v).strip() != "":
{indent}                return str(_v).strip()
{indent}        return None
{indent}
{indent}    def _s43_b2_parse_ts(_v):
{indent}        if _v is None:
{indent}            return 0.0
{indent}        _s = str(_v).strip()
{indent}        if not _s:
{indent}            return 0.0
{indent}        try:
{indent}            return float(_s)
{indent}        except Exception:
{indent}            pass
{indent}        try:
{indent}            if _s.endswith("Z"):
{indent}                _s = _s[:-1] + "+00:00"
{indent}            _dt = _s43_b2_datetime.fromisoformat(_s)
{indent}            if _dt.tzinfo is None:
{indent}                _dt = _dt.replace(tzinfo=_s43_b2_timezone.utc)
{indent}            return float(_dt.timestamp())
{indent}        except Exception:
{indent}            return 0.0
{indent}
{indent}    _slot_s = str(slot)
{indent}    _reg_raw = _s43_b2_first_env(
{indent}        "S43_WALLET_" + _slot_s + "_REGISTERED_AT",
{indent}        "S43_W" + _slot_s + "_REGISTERED_AT",
{indent}        "S43_TOKEN_REGISTERED_AT",
{indent}    )
{indent}    _exp_raw = _s43_b2_first_env(
{indent}        "S43_WALLET_" + _slot_s + "_EXPIRES_AT",
{indent}        "S43_W" + _slot_s + "_EXPIRES_AT",
{indent}        "S43_TOKEN_EXPIRES_AT",
{indent}    )
{indent}    _warn_raw = _s43_b2_first_env(
{indent}        "S43_WALLET_" + _slot_s + "_WARN_DAYS",
{indent}        "S43_W" + _slot_s + "_WARN_DAYS",
{indent}        "S43_TOKEN_WARN_DAYS",
{indent}    )
{indent}
{indent}    _now_ts = float(_s43_b2_time.time())
{indent}    _reg_ts = _s43_b2_parse_ts(_reg_raw)
{indent}    _exp_ts = _s43_b2_parse_ts(_exp_raw)
{indent}    try:
{indent}        _warn_days = float(_warn_raw) if _warn_raw is not None else 3.0
{indent}    except Exception:
{indent}        _warn_days = 3.0
{indent}
{indent}    if _reg_ts > 0:
{indent}        wr.token_registered_ts = _reg_ts
{indent}    if _exp_ts > 0:
{indent}        wr.token_expiry_ts = _exp_ts
{indent}
{indent}    wr.token_warn_days = _warn_days
{indent}
{indent}
{indent}    if _exp_ts > 0:
{indent}        _seconds_left = _exp_ts - _now_ts
{indent}        _days_left = _seconds_left / 86400.0
{indent}        wr.token_days_left = _days_left
{indent}
{indent}        if _seconds_left <= 0:
{indent}            wr.token_expiry_status = "EXPIRED"
{indent}            wr.token_expired = True
{indent}            wr.wallet_disabled = True
{indent}            wr.wallet_disable_reason = "TOKEN_EXPIRED"
{indent}        elif _days_left <= _warn_days:
{indent}            wr.token_expiry_status = "WARNING"
{indent}            wr.token_expired = False
{indent}            # فقط هشدار؛ wallet در حالت WARNING غیرفعال نمی‌شود.
{indent}        else:
{indent}            wr.token_expiry_status = "OK"
{indent}            wr.token_expired = False
{indent}    else:
{indent}        _days_left = -1.0
{indent}        wr.token_expiry_status = "UNKNOWN"
{indent}        wr.token_expired = False
{indent}
{indent}    _msg = (
{indent}        "event=WALLET_TOKEN_METADATA wallet=%s slot=%s status=%s "
{indent}        "registered_ts=%.3f expiry_ts=%.3f warn_days=%.1f days_left=%.2f disabled=%s reason=%s"
{indent}        % (
{indent}            wname,
{indent}            _slot_s,
{indent}            getattr(wr, "token_expiry_status", "UNKNOWN"),
{indent}            float(getattr(wr, "token_registered_ts", 0.0) or 0.0),
{indent}            float(getattr(wr, "token_expiry_ts", 0.0) or 0.0),
{indent}            float(getattr(wr, "token_warn_days", 3.0) or 3.0),
{indent}            float(getattr(wr, "token_days_left", _days_left) or _days_left),
{indent}            bool(getattr(wr, "wallet_disabled", False)),
{indent}            str(getattr(wr, "wallet_disable_reason", "") or ""),
{indent}        )
{indent}    )
{indent}    try:
{indent}        self._log.warning(_msg)
{indent}    except Exception:
{indent}        print(_msg)
{indent}except Exception as _s43_b2_e:
{indent}    try:
{indent}        self._log.error("event=WALLET_TOKEN_METADATA_ERROR wallet=%s error=%s", wname, str(_s43_b2_e))
{indent}    except Exception:
{indent}        print("event=WALLET_TOKEN_METADATA_ERROR wallet=%s error=%s" % (wname, str(_s43_b2_e)))
"""

new_src = src[:insert_pos] + block + src[insert_pos:]

bak = p.with_suffix(".py.bak.b2_runtime_inject")
bak.write_text(src, encoding="utf-8")
p.write_text(new_src, encoding="utf-8")

print("OK: injected runtime metadata block")
print("OK: backup:", bak)
