from pathlib import Path
import shutil
import time
import sys

patch_id = "wallet_runtime_duplicate_registration_guard_20260606"
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
lines = text.splitlines(keepends=True)

target_indexes = [i for i, line in enumerate(lines) if needle in line]
if len(target_indexes) != 1:
    print(f"STATUS=FAIL | REASON=unexpected_target_count | COUNT={len(target_indexes)}")
    raise SystemExit(2)

idx = target_indexes[0]
target_line = lines[idx]
indent = target_line[:len(target_line) - len(target_line.lstrip())]

guard_block = [
    f"{indent}# --- S43_PATCH: {patch_id} ---\n",
    f"{indent}_prev_wr = self.wallets.get(wname)\n",
    f"{indent}if _prev_wr is not None:\n",
    f"{indent}    try:\n",
    f"{indent}        logging.getLogger(__name__).warning(\n",
    f"{indent}            \"wallet_runtime_duplicate_registration %s\",\n",
    f"{indent}            {{\n",
    f"{indent}                \"wallet\": str(wname),\n",
    f"{indent}                \"existing_runtime_type\": type(_prev_wr).__name__,\n",
    f"{indent}                \"new_runtime_type\": type(wr).__name__,\n",
    f"{indent}            }}\n",
    f"{indent}        )\n",
    f"{indent}    except Exception:\n",
    f"{indent}        logging.getLogger(__name__).debug(\"wallet_runtime_duplicate_registration_audit_failed\", exc_info=True)\n",
    f"{indent}# --- /S43_PATCH: {patch_id} ---\n",
]

shutil.copy2(path, f"s43.py.bak.{patch_id}.{int(time.time())}")

new_lines = lines[:idx] + guard_block + lines[idx:]
path.write_text("".join(new_lines), encoding="utf-8", errors="surrogateescape")

print(f"STATUS=APPLIED | ID={patch_id}")
