from pathlib import Path
import shutil
import time
import sys

patch_id = "repair_wallet_runtime_log_sanitization_20260606"
path = Path("s43.py")

if not path.exists():
    print("STATUS=FAIL | REASON=s43.py_not_found")
    raise SystemExit(2)

text = path.read_text(encoding="utf-8", errors="surrogateescape")

bad_block = (
    '    # --- S43_PATCH: wallet_runtime_log_sanitization_patch_20260606 ---\n'
    '    _wallet_audit_safe = {\n'
    '        "wallet": str(_wallet_audit.get("wallet", "")),\n'
    '        "exchange": str(_wallet_audit.get("exchange", "")),\n'
    '        "token_expiry_ts": float(_wallet_audit.get("token_expiry_ts", 0.0) or 0.0),\n'
    '        "wallet_disabled": bool(_wallet_audit.get("wallet_disabled", False)),\n'
    '    }\n'
    '    logging.getLogger(__name__).info("wallet_runtime_registered %s", _wallet_audit_safe)\n'
    '    # --- /S43_PATCH: wallet_runtime_log_sanitization_patch_20260606 ---\n'
)

safe_line = (
    '    logging.getLogger(__name__).info("wallet_runtime_registered %s", {"wallet": str(_wallet_audit.get("wallet", "")), "exchange": str(_wallet_audit.get("exchange", "")), "token_expiry_ts": float(_wallet_audit.get("token_expiry_ts", 0.0) or 0.0), "wallet_disabled": bool(_wallet_audit.get("wallet_disabled", False))})\n'
)

already_safe = safe_line in text
has_bad_block = bad_block in text

if already_safe and not has_bad_block:
    print(f"STATUS=ALREADY_REPAIRED | ID={patch_id}")
    raise SystemExit(0)

shutil.copy2(path, f"s43.py.bak.{patch_id}.{int(time.time())}")

if has_bad_block:
    text = text.replace(bad_block, safe_line, 1)

original_line = '    logging.getLogger(__name__).info("wallet_runtime_registered %s", _wallet_audit)\n'
if original_line in text:
    text = text.replace(original_line, safe_line, 1)

path.write_text(text, encoding="utf-8", errors="surrogateescape")
print(f"STATUS=REPAIRED | ID={patch_id}")
