from pathlib import Path
from datetime import datetime
import shutil
import sys

TARGET = Path("s43.py")

if not TARGET.exists():
    print("ERROR: s43.py not found in current directory")
    sys.exit(1)

src = TARGET.read_text(encoding="utf-8", errors="ignore")

if "S43 Phase B2: Wallet token expiry metadata helpers" in src:
    print("INFO: Patch B2 already present, nothing to do")
    sys.exit(0)

helpers_block = r'''
# === S43 Phase B2: Wallet token expiry metadata helpers ===
def _s43_parse_ts_value(value):
    try:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value).strip()
        if not s:
            return 0.0
        try:
            return float(s)
        except Exception:
            pass
        try:
            from datetime import datetime, timezone
            normalized = s.replace("Z", "+00:00")
            try:
                dt = datetime.fromisoformat(normalized)
            except Exception:
                dt = datetime.strptime(s[:10], "%Y-%m-%d")
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return float(dt.timestamp())
        except Exception:
            return 0.0
    except Exception:
        return 0.0

def _s43_env_first(*names, default=None):
    try:
        import os
        for name in names:
            value = os.environ.get(name)
            if value is not None and str(value).strip() != "":
                return value
    except Exception:
        pass
    return default

def _s43_load_wallet_registry_json():
    try:
        import os, json
        path = (
            os.environ.get("S43_WALLET_REGISTRY_PATH")
            or os.environ.get("S43_WALLET_REGISTRY_JSON")
            or ""
        )
        if not path:
            return {}
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}

def _s43_registry_entry_for_slot(slot):
    try:
        data = _s43_load_wallet_registry_json()
        if not isinstance(data, dict):
            return {}
        root = data.get("wallets") if isinstance(data.get("wallets"), dict) else data
        keys = [f"W{slot}", str(slot), f"wallet_{slot}", f"slot_{slot}"]
        for key in keys:
            entry = root.get(key)
            if isinstance(entry, dict):
                return entry
    except Exception:
        pass
    return {}

def _s43_wallet_token_metadata(slot):
    try:
        entry = _s43_registry_entry_for_slot(slot)

        registered_raw = _s43_env_first(
            f"S43_WALLET_{slot}_REGISTERED_AT",
            f"S43_W{slot}_REGISTERED_AT",
            "S43_TOKEN_REGISTERED_AT",
            "S43_WALLET_REGISTERED_AT",
            default=entry.get("registered_at") or entry.get("token_registered_at"),
        )

        expires_raw = _s43_env_first(
            f"S43_WALLET_{slot}_EXPIRES_AT",
            f"S43_W{slot}_EXPIRES_AT",
            "S43_TOKEN_EXPIRES_AT",
            "S43_WALLET_EXPIRES_AT",
            default=entry.get("expires_at") or entry.get("token_expires_at") or entry.get("expiry_at"),
        )

        warn_raw = _s43_env_first(
            f"S43_WALLET_{slot}_WARN_DAYS",
            f"S43_W{slot}_WARN_DAYS",
            "S43_TOKEN_WARN_DAYS",
            "S43_WALLET_WARN_DAYS",
            default=entry.get("warn_days", 7),
        )

        registered_ts = _s43_parse_ts_value(registered_raw)
        expiry_ts = _s43_parse_ts_value(expires_raw)

        try:
            warn_days = int(float(warn_raw))
        except Exception:
            warn_days = 7

        if warn_days < 0:
            warn_days = 0

        return {
            "registered_ts": float(registered_ts or 0.0),
            "expiry_ts": float(expiry_ts or 0.0),
            "warn_days": int(warn_days),
            "source": "env_or_registry",
        }
    except Exception:
        return {
            "registered_ts": 0.0,
            "expiry_ts": 0.0,
            "warn_days": 7,
            "source": "fallback",
        }

def _s43_apply_wallet_token_metadata(wr, slot, log=None):
    try:
        import time
        meta = _s43_wallet_token_metadata(slot)
        registered_ts = float(meta.get("registered_ts") or 0.0)
        expiry_ts = float(meta.get("expiry_ts") or 0.0)
        warn_days = int(meta.get("warn_days") or 7)
        source = str(meta.get("source") or "unknown")
        now = time.time()

        days_left = 0.0
        state = "UNKNOWN"

        if expiry_ts > 0:
            days_left = (expiry_ts - now) / 86400.0
            if days_left <= 0:
                state = "EXPIRED"
            elif days_left <= float(warn_days):
                state = "WARNING"
            else:
                state = "OK"

        try:
            wr.token_registered_ts = registered_ts
        except Exception:
            pass
        try:
            wr.token_warn_days = warn_days
        except Exception:
            pass
        try:
            wr.token_days_left = float(days_left)
        except Exception:
            pass
        try:
            wr.token_expiry_state = state
        except Exception:
            pass
        try:
            wr.token_expiry_source = source
        except Exception:
            pass
        if expiry_ts > 0:
            try:
                wr.token_expiry_ts = expiry_ts
            except Exception:
                pass
        if state == "EXPIRED":
            try:
                wr.wallet_disabled = True
            except Exception:
                pass
            try:
                wr.wallet_disable_reason = "TOKEN_EXPIRED"
            except Exception:
                pass
        try:
            if log is not None:
                log.info(
                    "event=WALLET_TOKEN_METADATA wallet=W%s state=%s days_left=%.2f warn_days=%s source=%s",
                    slot, state, float(days_left), warn_days, source
                )
        except Exception:
            pass
        return wr
    except Exception as e:
        try:
            if log is not None:
                log.warning("event=WALLET_TOKEN_METADATA_FAILED wallet=W%s err=%s", slot, e)
        except Exception:
            pass
        return wr
'''

runtime_fields_block = '''
        # S43 Phase B2: token registry/expiry metadata
        self.token_registered_ts = 0.0
        self.token_warn_days = 7
        self.token_days_left = 0.0
        self.token_expiry_state = "UNKNOWN"
        self.token_expiry_source = ""
'''

apply_block = '''
        # S43 Phase B2: attach token expiry metadata to WalletRuntime
        try:
            _s43_apply_wallet_token_metadata(wr, slot, getattr(self, "_log", None))
        except Exception:
            pass
'''

changed = False

main_guard = '\nif __name__ == "__main__":'
if main_guard in src:
    src = src.replace(main_guard, "\n" + helpers_block + "\n" + main_guard, 1)
    changed = True
else:
    print("ERROR: could not find main guard for helper injection")
    sys.exit(2)

if 'self.wallet_disable_reason = ""' in src and 'self.token_registered_ts = 0.0' not in src:
    src = src.replace(
        'self.wallet_disable_reason = ""',
        'self.wallet_disable_reason = ""' + runtime_fields_block,
        1
    )
    changed = True
elif 'self.token_registered_ts = 0.0' in src:
    print("INFO: runtime fields already present")
else:
    print("WARN: could not inject runtime fields automatically")

needle_variants = [
    'self.wallets[slot] = wr',
    'self.wallets[wallet_slot] = wr',
]

injected_apply = False
for needle in needle_variants:
    if needle in src and "_s43_apply_wallet_token_metadata(wr, slot" not in src:
        src = src.replace(needle, apply_block + "\n        " + needle, 1)
        injected_apply = True
        changed = True
        break

if not injected_apply:
    if "_s43_apply_wallet_token_metadata(wr, slot" in src:
        print("INFO: apply block already present")
    else:
        print("WARN: could not inject apply block automatically")

if not changed:
    print("INFO: no changes were necessary")
    sys.exit(0)

backup = TARGET.with_name(f"s43.py.bak.patch_b2.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
shutil.copy2(TARGET, backup)
TARGET.write_text(src, encoding="utf-8")

print(f"OK: patch applied to {TARGET}")
print(f"OK: backup created at {backup}")
