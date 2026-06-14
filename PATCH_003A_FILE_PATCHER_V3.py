# PATCH_003A_FILE_PATCHER_V3.py
# Purpose:
#   Apply PATCH_003A_PERFORMANCE_LEDGER_BASELINE to s43.py safely.
#
# Safety:
#   - Passive logging only.
#   - No trading decision changes.
#   - No order behavior changes.
#   - No modification to return {} logic.
#   - All runtime hooks are wrapped in try/except.
#   - Automatic rollback on failure.

from __future__ import annotations

import hashlib
import os
import py_compile
import shutil
import sys
import time
from pathlib import Path


PATCH_NAME = "PATCH_003A_PERFORMANCE_LEDGER_BASELINE"
TARGET_FILE = Path("s43.py")

EXPECTED_SHA256 = "15DF1D50DE507862FF69B2393A3F09DDDE5927CB0F5E55BCAF9C192FC22BE59C"

MARKERS = [
    "PATCH_003A_PERFORMANCE_LEDGER_BASELINE",
    "_patch003a_perf_ledger_event",
    "ORDER_SUBMIT_CANDIDATE",
    "GOVERNANCE_GATE_BLOCKED",
    "AI_LIVE_TRADING_BLOCKED",
]

PHASE4_ANCHOR = "PHASE4_ORDER_GATE_MAIN"
AI_ANCHOR = "AI_LIVE_TRADING"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def detect_newline(raw: bytes) -> str:
    if b"\r\n" in raw:
        return "\r\n"
    return "\n"


def read_text_preserve(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    newline = detect_newline(raw)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8-sig")
    return text, newline


def write_text_utf8(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def split_keep_structure(text: str) -> list[str]:
    return text.splitlines()


def join_lines(lines: list[str], newline: str) -> str:
    return newline.join(lines) + newline


def find_place_order_signature_end(lines: list[str]) -> int:
    start = None
    for i, line in enumerate(lines):
        if line.startswith("    async def place_order("):
            start = i
            break

    if start is None:
        fail("Anchor not found: async def place_order(")

    for j in range(start, min(start + 80, len(lines))):
        stripped = lines[j].strip()
        if stripped.endswith(") -> dict:") or stripped == ") -> dict:":
            return j

    fail("Could not find end of place_order signature.")
    return -1


def skip_initial_docstring_or_blank(lines: list[str], body_start: int) -> int:
    """
    Returns insertion index inside function body.

    We avoid placing code before an immediate function docstring if one exists.
    This preserves function __doc__ metadata as much as possible.
    """
    i = body_start

    while i < len(lines) and lines[i].strip() == "":
        i += 1

    if i >= len(lines):
        return body_start

    stripped = lines[i].lstrip()

    triple_markers = ('"""', "'''")

    for q in triple_markers:
        if stripped.startswith(q):
            # One-line docstring
            if stripped.count(q) >= 2 and len(stripped) > len(q):
                return i + 1

            # Multi-line docstring
            i += 1
            while i < len(lines):
                if q in lines[i]:
                    return i + 1
                i += 1

            fail("Unterminated docstring after place_order signature.")

    return body_start


def find_first_return_after_anchor(
    lines: list[str],
    anchor: str,
    search_limit: int = 80,
) -> int:
    anchor_index = None

    for i, line in enumerate(lines):
        if anchor in line:
            anchor_index = i
            break

    if anchor_index is None:
        fail(f"Anchor not found: {anchor}")

    end = min(anchor_index + search_limit, len(lines))

    for j in range(anchor_index + 1, end):
        if lines[j].strip() == "return {}":
            return j

    fail(f"Could not find return {{}} after anchor: {anchor}")
    return -1


def already_patched(text: str) -> bool:
    return any(marker in text for marker in MARKERS)


def ensure_clean_markers(text: str) -> None:
    found = [m for m in MARKERS if m in text]
    if found:
        fail(
            "Patch markers already exist in target file. "
            "Refusing to continue. Found: " + ", ".join(found)
        )


def make_entry_block() -> list[str]:
    return [
        "        # PATCH_003A_PERFORMANCE_LEDGER_BASELINE: passive performance ledger helper",
        "        def _patch003a_perf_ledger_event(_event, **_fields):",
        "            try:",
        "                _os = __import__('os')",
        "                _json = __import__('json')",
        "                _time = __import__('time')",
        "                _path = _os.path.join(_os.getcwd(), 'PATCH_003A_PERFORMANCE_LEDGER.jsonl')",
        "                _payload = {",
        "                    'patch': 'PATCH_003A_PERFORMANCE_LEDGER_BASELINE',",
        "                    'event': str(_event),",
        "                    'ts': _time.time(),",
        "                }",
        "                try:",
        "                    _payload.update(_fields)",
        "                except Exception:",
        "                    pass",
        "                with open(_path, 'a', encoding='utf-8') as _f:",
        "                    _f.write(_json.dumps(_payload, ensure_ascii=False, default=str) + '\\n')",
        "            except Exception:",
        "                pass",
        "",
        "        # PATCH_003A_PERFORMANCE_LEDGER_BASELINE: ORDER_SUBMIT_CANDIDATE",
        "        try:",
        "            _patch003a_perf_ledger_event(",
        "                'ORDER_SUBMIT_CANDIDATE',",
        "                symbol=locals().get('symbol', None),",
        "                side=locals().get('side', None),",
        "                amount=locals().get('amount', None),",
        "                price=locals().get('price', None),",
        "                order_type=locals().get('order_type', None),",
        "            )",
        "        except Exception:",
        "            pass",
        "",
    ]


def make_gate_block(event_name: str, base_indent: str) -> list[str]:
    return [
        f"{base_indent}# PATCH_003A_PERFORMANCE_LEDGER_BASELINE: {event_name}",
        f"{base_indent}try:",
        f"{base_indent}    _patch003a_perf_ledger_event(",
        f"{base_indent}        '{event_name}',",
        f"{base_indent}        symbol=locals().get('symbol', None),",
        f"{base_indent}        side=locals().get('side', None),",
        f"{base_indent}        amount=locals().get('amount', None),",
        f"{base_indent}        price=locals().get('price', None),",
        f"{base_indent}        order_type=locals().get('order_type', None),",
        f"{base_indent}    )",
        f"{base_indent}except Exception:",
        f"{base_indent}    pass",
    ]


def apply_patch_to_text(text: str, newline: str) -> str:
    ensure_clean_markers(text)

    lines = split_keep_structure(text)

    sig_end = find_place_order_signature_end(lines)
    entry_insert_at = skip_initial_docstring_or_blank(lines, sig_end + 1)

    phase4_return_idx = find_first_return_after_anchor(lines, PHASE4_ANCHOR)
    ai_return_idx = find_first_return_after_anchor(lines, AI_ANCHOR)

    if not (sig_end < phase4_return_idx < ai_return_idx):
        fail(
            "Unexpected anchor order. Expected: place_order signature < PHASE4 return < AI return."
        )

    # Insert from bottom to top where possible to avoid index shifting.
    ai_indent = lines[ai_return_idx][: len(lines[ai_return_idx]) - len(lines[ai_return_idx].lstrip())]
    phase4_indent = lines[phase4_return_idx][: len(lines[phase4_return_idx]) - len(lines[phase4_return_idx].lstrip())]

    ai_block = make_gate_block("AI_LIVE_TRADING_BLOCKED", ai_indent)
    phase4_block = make_gate_block("GOVERNANCE_GATE_BLOCKED", phase4_indent)
    entry_block = make_entry_block()

    # AI block before AI return {}
    lines[ai_return_idx:ai_return_idx] = ai_block

    # PHASE4 index unchanged because it is before AI insertion.
    lines[phase4_return_idx:phase4_return_idx] = phase4_block

    # Entry index unchanged because it is before both gate insertions.
    lines[entry_insert_at:entry_insert_at] = entry_block

    patched = join_lines(lines, newline)

    # Final marker sanity check.
    required_after = [
        "PATCH_003A_PERFORMANCE_LEDGER_BASELINE",
        "_patch003a_perf_ledger_event",
        "ORDER_SUBMIT_CANDIDATE",
        "GOVERNANCE_GATE_BLOCKED",
        "AI_LIVE_TRADING_BLOCKED",
    ]

    missing = [m for m in required_after if m not in patched]
    if missing:
        fail("Patch construction failed. Missing markers after patch: " + ", ".join(missing))

    return patched


def compile_check(path: Path) -> None:
    py_compile.compile(str(path), doraise=True)


def main() -> int:
    print("=" * 72)
    print("PATCH_003A_FILE_PATCHER_V3")
    print("=" * 72)

    if not TARGET_FILE.exists():
        fail(f"Target file not found: {TARGET_FILE}")

    before_sha = sha256_file(TARGET_FILE)
    print(f"[INFO] Target: {TARGET_FILE}")
    print(f"[INFO] SHA256 before: {before_sha}")

    if before_sha != EXPECTED_SHA256:
        fail(
            "SHA256 mismatch. Refusing to patch.\n"
            f"Expected: {EXPECTED_SHA256}\n"
            f"Actual:   {before_sha}\n"
            "This protects against patching the wrong or already-modified file."
        )

    print("[INFO] Baseline SHA256 verified.")

    text, newline = read_text_preserve(TARGET_FILE)

    if already_patched(text):
        ensure_clean_markers(text)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = Path(f"s43.py.PATCH_003A_V3_BACKUP_{timestamp}.bak")

    shutil.copy2(TARGET_FILE, backup_path)
    print(f"[INFO] Backup created: {backup_path}")

    try:
        patched_text = apply_patch_to_text(text, newline)

        write_text_utf8(TARGET_FILE, patched_text)
        print("[INFO] Patched text written.")

        print("[INFO] Running py_compile...")
        compile_check(TARGET_FILE)
        print("[INFO] py_compile: PASS")

        after_sha = sha256_file(TARGET_FILE)
        print(f"[INFO] SHA256 after:  {after_sha}")

        if after_sha == before_sha:
            fail("SHA256 did not change after patch. Unexpected no-op.")

        print("=" * 72)
        print("PATCH SUCCESS")
        print("=" * 72)
        print(f"Patch:      {PATCH_NAME}")
        print(f"Backup:     {backup_path}")
        print(f"Ledger log: PATCH_003A_PERFORMANCE_LEDGER.jsonl")
        print("")
        print("Next recommended checks:")
        print("  python -m py_compile .\\s43.py")
        print("  Select-String -Path .\\s43.py -Pattern \"PATCH_003A_PERFORMANCE_LEDGER_BASELINE|_patch003a_perf_ledger_event|ORDER_SUBMIT_CANDIDATE|GOVERNANCE_GATE_BLOCKED|AI_LIVE_TRADING_BLOCKED\"")
        print("")
        return 0

    except Exception as exc:
        print("=" * 72)
        print("PATCH FAILED - ROLLING BACK")
        print("=" * 72)
        print(f"[ERROR] {exc}")

        try:
            shutil.copy2(backup_path, TARGET_FILE)
            print(f"[ROLLBACK] Restored from: {backup_path}")

            rollback_sha = sha256_file(TARGET_FILE)
            print(f"[ROLLBACK] SHA256 restored: {rollback_sha}")

            try:
                compile_check(TARGET_FILE)
                print("[ROLLBACK] py_compile after rollback: PASS")
            except Exception as compile_exc:
                print(f"[ROLLBACK WARNING] py_compile after rollback failed: {compile_exc}")

        except Exception as rb_exc:
            print(f"[CRITICAL] Rollback failed: {rb_exc}")

        return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print("=" * 72)
        print("FATAL ERROR")
        print("=" * 72)
        print(str(e))
        raise SystemExit(1)
