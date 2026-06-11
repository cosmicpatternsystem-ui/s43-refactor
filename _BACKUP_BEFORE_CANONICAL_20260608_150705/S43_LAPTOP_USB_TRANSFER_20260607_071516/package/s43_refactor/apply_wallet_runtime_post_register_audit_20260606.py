from pathlib import Path
import shutil
import time
import sys

patch_id = "wallet_runtime_post_register_audit_20260606"
path = Path("s43.py")

if not path.exists():
    print("STATUS=FAIL | REASON=s43.py_not_found")
    raise SystemExit(2)

text = path.read_text(encoding="utf-8", errors="surrogateescape")
start_marker = f"# --- S43_PATCH: {patch_id} ---"

if start_marker in text:
    print(f"STATUS=ALREADY_PRESENT | ID={patch_id}")
    raise SystemExit(0)

needle = "self.wallets[wname] = wr"
shutil.copy2(path, f"s43.py.bak.{patch_id}.{int(time.time())}")

lines = text.splitlines(keepends=True)
out = []
inserted = False

for line in lines:
    out.append(line)
    if (not inserted) and needle in line:
        indent = line[:len(line) - len(line.lstrip())]
        out.extend([
            f"{indent}{start_marker}\n",
            f"{indent}try:\n",
            f"{indent}    _wallet_audit = {{\n",
            f"{indent}        \"wallet\": str(wname),\n",
            f"{indent}        \"exchange\": str(getattr(ex, \"name\", getattr(ex, \"exchange\", \"\"))),\n",
            f"{indent}        \"token_expiry_ts\": float(token_expiry_ts) if token_expiry_ts is not None else 0.0,\n",
            f"{indent}        \"wallet_disabled\": bool(wallet_disabled),\n",
            f"{indent}    }}\n",
            f"{indent}    logging.getLogger(__name__).info(\"wallet_runtime_registered %s\", _wallet_audit)\n",
            f"{indent}except Exception:\n",
            f"{indent}    logging.getLogger(__name__).debug(\"wallet_runtime_post_register_audit_failed\", exc_info=True)\n",
            f"{indent}# --- /S43_PATCH: {patch_id} ---\n",
        ])
        inserted = True

if not inserted:
    print("STATUS=FAIL | REASON=target_line_not_found")
    raise SystemExit(2)

path.write_text("".join(out), encoding="utf-8", errors="surrogateescape")
print(f"STATUS=APPLIED | ID={patch_id}")
