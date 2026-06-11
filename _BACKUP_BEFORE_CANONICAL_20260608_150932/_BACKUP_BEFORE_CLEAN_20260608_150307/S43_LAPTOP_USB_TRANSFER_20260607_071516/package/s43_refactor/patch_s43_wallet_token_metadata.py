#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil
import py_compile
import sys

TARGET = Path("s43.py")

MARKER = "S43 PATCH B2 RUNTIME TOKEN METADATA INJECT"

NEEDLE = '''            self.wallets[wname] = wr
            try:
                wr.token_expiry_ts = float(token_expiry_ts or 0)
                wr.wallet_disabled = bool(wallet_disabled)
                wr.wallet_disable_reason = str(wallet_disable_reason or "")
            except Exception:
                pass
'''

INJECT = '''            # S43 PATCH B2 RUNTIME TOKEN METADATA INJECT
            try:
                import os
                import time
                from datetime import datetime, timezone

                def _s43_parse_env_ts(v):
                    if v is None:
                        return 0.0
                    s = str(v).strip()
                    if not s:
                        return 0.0
                    try:
                        return float(s)
                    except Exception:
                        pass
                    try:
                        if s.endswith("Z"):
                            s = s[:-1] + "+00:00"
                        dt = datetime.fromisoformat(s)
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        return float(dt.timestamp())
                    except Exception:
                        return 0.0

                slot_s = str(slot)

                reg_raw = (
                    os.environ.get(f"S43_WALLET_{slot_s}_REGISTERED_AT")
                    or os.environ.get(f"S43_W{slot_s}_REGISTERED_AT")
                    or os.environ.get("S43_TOKEN_REGISTERED_AT")
                )
                exp_raw = (
                    os.environ.get(f"S43_WALLET_{slot_s}_EXPIRES_AT")
                    or os.environ.get(f"S43_W{slot_s}_EXPIRES_AT")
                    or os.environ.get("S43_TOKEN_EXPIRES_AT")
                )
                warn_raw = (
                    os.environ.get(f"S43_WALLET_{slot_s}_WARN_DAYS")
                    or os.environ.get(f"S43_W{slot_s}_WARN_DAYS")
                    or os.environ.get("S43_TOKEN_WARN_DAYS")
                )

                reg_ts = _s43_parse_env_ts(reg_raw)
                exp_ts = _s43_parse_env_ts(exp_raw)

                try:
                    warn_days = float(warn_raw) if warn_raw is not None else 3.0
                except Exception:
                    warn_days = 3.0

                now_ts = float(time.time())

                if reg_ts > 0:
                    wr.token_registered_ts = reg_ts
                if exp_ts > 0:
                    wr.token_expiry_ts = exp_ts

                wr.token_warn_days = warn_days

                if exp_ts > 0:
                    days_left = (exp_ts - now_ts) / 86400.0
                    wr.token_days_left = days_left

                    if exp_ts <= now_ts:
                        wr.token_expiry_status = "EXPIRED"
                        wr.token_expired = True
                        wr.wallet_disabled = True
                        wr.wallet_disable_reason = "TOKEN_EXPIRED"
                    elif days_left <= warn_days:
                        wr.token_expiry_status = "WARNING"
                        wr.token_expired = False
                    else:
                        wr.token_expiry_status = "OK"
                        wr.token_expired = False
                else:
                    wr.token_expiry_status = "UNKNOWN"
                    wr.token_expired = False
                    wr.token_days_left = -1.0

                try:
                    self._log.warning(
                        "event=WALLET_TOKEN_METADATA wallet=%s slot=%s status=%s registered_ts=%.3f expiry_ts=%.3f warn_days=%.1f days_left=%.2f disabled=%s reason=%s",
                        wname,
                        slot_s,
                        str(getattr(wr, "token_expiry_status", "UNKNOWN")),
                        float(getattr(wr, "token_registered_ts", 0.0) or 0.0),
                        float(getattr(wr, "token_expiry_ts", 0.0) or 0.0),
                        float(getattr(wr, "token_warn_days", 3.0) or 3.0),
                        float(getattr(wr, "token_days_left", -1.0) or -1.0),
                        bool(getattr(wr, "wallet_disabled", False)),
                        str(getattr(wr, "wallet_disable_reason", "") or ""),
                    )
                except Exception:
                    pass

            except Exception as e:
                try:
                    self._log.error("event=WALLET_TOKEN_METADATA_ERROR wallet=%s error=%s", wname, str(e))
                except Exception:
                    pass

'''

def main():
    if not TARGET.exists():
        print("[ERR] s43.py not found in current directory")
        print("[HINT] cd into the directory that contains s43.py, then run again")
        return 2

    text = TARGET.read_text(encoding="utf-8", errors="replace")

    if MARKER in text:
        print("[OK] Patch marker already exists. Nothing to do.")
        try:
            py_compile.compile(str(TARGET), doraise=True)
            print("[OK] py_compile passed")
            return 0
        except Exception as e:
            print("[ERR] py_compile failed after existing patch:")
            print(e)
            return 3

    count = text.count(NEEDLE)
    if count != 1:
        print(f"[ERR] Expected exact insertion block once, found {count}")
        print("[INFO] Searching nearby occurrences of 'self.wallets[wname] = wr' ...")
        lines = text.splitlines()
        hits = [i + 1 for i, line in enumerate(lines) if "self.wallets[wname] = wr" in line]
        print("[INFO] Hits:", hits)
        if hits:
            for ln in hits[:5]:
                start = max(1, ln - 5)
                end = min(len(lines), ln + 12)
                print(f"--- context {start}:{end} ---")
                for n in range(start, end + 1):
                    print(f"{n}: {lines[n-1]}")
        return 4

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_name(f"s43.py.bak.b2_token_metadata.{stamp}")
    shutil.copy2(TARGET, backup)
    print(f"[OK] Backup created: {backup}")

    new_text = text.replace(NEEDLE, NEEDLE + INJECT, 1)
    TARGET.write_text(new_text, encoding="utf-8")
    print("[OK] Patch injected")

    try:
        py_compile.compile(str(TARGET), doraise=True)
        print("[OK] py_compile passed")
    except Exception as e:
        print("[ERR] py_compile failed. Restoring backup...")
        shutil.copy2(backup, TARGET)
        print("[OK] Backup restored")
        print("[ERR]", e)
        return 5

    print("[DONE] S43 wallet token metadata patch applied successfully")
    print("[NEXT] Run:")
    print("       grep -n 'S43 PATCH B2 RUNTIME TOKEN METADATA INJECT\\|WALLET_TOKEN_METADATA' s43.py")
    return 0

if __name__ == "__main__":
    sys.exit(main())
