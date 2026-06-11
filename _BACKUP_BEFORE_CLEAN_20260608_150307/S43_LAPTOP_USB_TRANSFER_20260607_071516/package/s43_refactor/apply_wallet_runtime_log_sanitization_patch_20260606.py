from pathlib import Path
import shutil
import time
import re
import sys

patch_id = "wallet_runtime_log_sanitization_patch_20260606"
path = Path("s43.py")

if not path.exists():
    print("STATUS=FAIL | REASON=s43.py_not_found")
    raise SystemExit(2)

text = path.read_text(encoding="utf-8", errors="surrogateescape")

start_marker = f"# --- S43_PATCH: {patch_id} ---"
if start_marker in text:
    print(f"STATUS=ALREADY_PRESENT | ID={patch_id}")
    raise SystemExit(0)

anchor_marker = "# --- S43_PATCH: wallet_runtime_post_register_audit_20260606 ---"
if anchor_marker not in text:
    print("STATUS=FAIL | REASON=anchor_patch_not_found")
    raise SystemExit(2)

old_snippet = (
    '    logging.getLogger(__name__).info("wallet_runtime_registered %s", _wallet_audit)\n'
)

if old_snippet not in text:
    if '"wallet_runtime_registered %s", _wallet_audit' not in text:
        print("STATUS=FAIL | REASON=target_log_line_not_found")
        raise SystemExit(2)

replacement = (
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

count = text.count(old_snippet)
if count != 1:
    print(f"STATUS=FAIL | REASON=unexpected_target_count | COUNT={count}")
    raise SystemExit(2)

shutil.copy2(path, f"s43.py.bak.{patch_id}.{int(time.time())}")
text = text.replace(old_snippet, replacement, 1)
path.write_text(text, encoding="utf-8", errors="surrogateescape")

print(f"STATUS=APPLIED | ID={patch_id}")
