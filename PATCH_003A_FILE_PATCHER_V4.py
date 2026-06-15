# PATCH_003A_FILE_PATCHER_V4.py
# Purpose:
#   Apply PATCH_003A_PERFORMANCE_LEDGER_BASELINE to s43.py safely.
#
# V4 improvements over V3:
#   - Finds place_order as a bounded region.
#   - Finds PHASE4 return {} inside place_order.
#   - Finds AI return {} using AI anchors if available.
#   - Falls back to the next return {} after PHASE4 return within place_order.
#
# Safety:
#   - Passive logging only.
#   - No trading decision changes.
#   - No order behavior changes.
#   - No modification to existing return {} statements.
#   - All runtime hooks are wrapped in try/except.
#   - Automatic rollback on failure.

from __future__ import annotations

import hashlib
import py_compile
import shutil
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

AI_ANCHOR_CANDIDATES = [
    "AI_LIVE_TRADING",
    "LIVE_TRADING",
    "live trading",
    "ai_live",
    "AI live",
]


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


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


def join_lines(lines: list[str], newline: str) -> str:
    return newline.join(lines) + newline


def line_indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def ensure_no_existing_markers(text: str) -> None:
    found = [m for m in MARKERS if m in text]
    if found:
        fail(
            "Patch markers already exist in target file. "
            "Refusing to continue. Found: " + ", ".join(found)
        )


def find_place_order_bounds(lines: list[str]) -> tuple[int, int, int]:
    """
    Returns:
        def_start_index, signature_end_index, function_end_index_exclusive

    Assumption confirmed by discovery:
        place_order is a class method indented with 4 spaces.
    """

    def_start = None

    for i, line in enumerate(lines):
        if line.startswith("    async def place_order("):
            def_start = i
            break

    if def_start is None:
        fail("Could not find place_order definition: '    async def place_order('")

    signature_end = None

    for j in range(def_start, min(def_start + 120, len(lines))):
        stripped = lines[j].strip()
        if stripped.endswith(") -> dict:") or stripped == ") -> dict:":
            signature_end = j
            break

    if signature_end is None:
        fail("Could not find end of place_order signature.")

    # Find next method/class-level definition at same indentation.
    # place_order itself has 4-space indentation.
    function_end = len(lines)

    for k in range(signature_end + 1, len(lines)):
        line = lines[k]

        if line.startswith("    async def ") and k > def_start:
            function_end = k
            break

        if line.startswith("    def ") and k > def_start:
            function_end = k
            break

        if line.startswith("class ") and k > def_start:
            function_end = k
            break

    if function_end <= signature_end:
        fail("Invalid place_order bounds detected.")

    return def_start, signature_end, function_end


def skip_initial_docstring_or_blank(lines: list[str], body_start: int, function_end: int) -> int:
    """
    Returns safe insertion index inside place_order body.

    If the function has an immediate docstring, insert after it to preserve __doc__.
    """

    i = body_start

    while i < function_end and lines[i].strip() == "":
        i += 1

    if i >= function_end:
        return body_start

    stripped = lines[i].lstrip()

    for q in ('"""', "'''"):
        if stripped.startswith(q):
            # Single-line docstring.
            if stripped.count(q) >= 2 and len(stripped) > len(q):
                return i + 1

            # Multi-line docstring.
            i += 1
            while i < function_end:
                if q in lines[i]:
                    return i + 1
                i += 1

            fail("Unterminated docstring in place_order.")

    return body_start


def find_anchor_in_range(
    lines: list[str],
    start: int,
    end: int,
    anchor: str,
) -> int | None:
    for i in range(start, end):
        if anchor in lines[i]:
            return i
    return None


def find_first_return_empty_after(
    lines: list[str],
    start: int,
    end: int,
) -> int | None:
    for i in range(start, end):
        if lines[i].strip() == "return {}":
            return i
    return None


def find_all_return_empty_in_range(
    lines: list[str],
    start: int,
    end: int,
) -> list[int]:
    return [i for i in range(start, end) if lines[i].strip() == "return {}"]


def find_phase4_and_ai_returns(
    lines: list[str],
    signature_end: int,
    function_end: int,
) -> tuple[int, int]:
    """
    Robust return finder.

    PHASE4:
        Find PHASE4_ORDER_GATE_MAIN anchor, then first return {} after it.

    AI:
        Prefer AI anchor candidates after PHASE4 return.
        If none found or no return after AI anchor, use first return {} after PHASE4 return.

    This matches the discovered structure:
        PHASE4 return {} around line 3272
        AI return {} around line 3287
    """

    phase4_anchor_idx = find_anchor_in_range(
        lines,
        signature_end + 1,
        function_end,
        PHASE4_ANCHOR,
    )

    if phase4_anchor_idx is None:
        fail(f"Could not find PHASE4 anchor inside place_order: {PHASE4_ANCHOR}")

    phase4_return_idx = find_first_return_empty_after(
        lines,
        phase4_anchor_idx + 1,
        function_end,
    )

    if phase4_return_idx is None:
        fail("Could not find PHASE4 return {} after PHASE4 anchor.")

    # First attempt: find AI anchor candidate after PHASE4 return.
    ai_anchor_idx = None
    ai_anchor_used = None

    for candidate in AI_ANCHOR_CANDIDATES:
        idx = find_anchor_in_range(
            lines,
            phase4_return_idx + 1,
            function_end,
            candidate,
        )
        if idx is not None:
            ai_anchor_idx = idx
            ai_anchor_used = candidate
            break

    ai_return_idx = None

    if ai_anchor_idx is not None:
        ai_return_idx = find_first_return_empty_after(
            lines,
            ai_anchor_idx + 1,
            function_end,
        )

        if ai_return_idx is not None:
            print(f"[INFO] AI anchor used: {ai_anchor_used!r} at line index {ai_anchor_idx + 1}")

    # Fallback: first return {} after PHASE4 return.
    if ai_return_idx is None:
        print("[WARN] AI anchor return not found. Falling back to next return {} after PHASE4 return.")
        ai_return_idx = find_first_return_empty_after(
            lines,
            phase4_return_idx + 1,
            function_end,
        )

    if ai_return_idx is None:
        returns = find_all_return_empty_in_range(lines, signature_end + 1, function_end)
        fail(
            "Could not find AI return {} after PHASE4 return. "
            f"All return {{}} indices inside place_order: {[r + 1 for r in returns]}"
        )

    if not (signature_end < phase4_return_idx < ai_return_idx < function_end):
        fail(
            "Unexpected return order. Expected: signature_end < PHASE4 return < AI return < function_end. "
            f"signature_end={signature_end + 1}, "
            f"phase4_return={phase4_return_idx + 1}, "
            f"ai_return={ai_return_idx + 1}, "
            f"function_end={function_end + 1}"
        )

    # Extra safety: the two selected returns must be different lines.
    if phase4_return_idx == ai_return_idx:
        fail("PHASE4 return and AI return resolved to same line. Refusing to patch.")

    print(f"[INFO] PHASE4 return selected at line index: {phase4_return_idx + 1}")
    print(f"[INFO] AI return selected at line index:     {ai_return_idx + 1}")

    return phase4_return_idx, ai_return_idx


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
    ensure_no_existing_markers(text)

    lines = text.splitlines()

    def_start, signature_end, function_end = find_place_order_bounds(lines)

    print(f"[INFO] place_order def start line index:      {def_start + 1}")
    print(f"[INFO] place_order signature end line index:  {signature_end + 1}")
    print(f"[INFO] place_order function end line index:   {function_end + 1}")

    entry_insert_at = skip_initial_docstring_or_blank(
        lines,
        signature_end + 1,
        function_end,
    )

    phase4_return_idx, ai_return_idx = find_phase4_and_ai_returns(
        lines,
        signature_end,
        function_end,
    )

    # Determine exact indentation from existing return {} lines.
    phase4_indent = line_indent(lines[phase4_return_idx])
    ai_indent = line_indent(lines[ai_return_idx])

    if len(phase4_indent) < 8:
        fail("PHASE4 return indentation looks unsafe/too shallow.")

    if len(ai_indent) < 8:
        fail("AI return indentation looks unsafe/too shallow.")

    entry_block = make_entry_block()
    phase4_block = make_gate_block("GOVERNANCE_GATE_BLOCKED", phase4_indent)
    ai_block = make_gate_block("AI_LIVE_TRADING_BLOCKED", ai_indent)

    # Insert from bottom to top to keep indices stable.
    lines[ai_return_idx:ai_return_idx] = ai_block
    lines[phase4_return_idx:phase4_return_idx] = phase4_block
    lines[entry_insert_at:entry_insert_at] = entry_block

    patched_text = join_lines(lines, newline)

    required_after = [
        "PATCH_003A_PERFORMANCE_LEDGER_BASELINE",
        "_patch003a_perf_ledger_event",
        "ORDER_SUBMIT_CANDIDATE",
        "GOVERNANCE_GATE_BLOCKED",
        "AI_LIVE_TRADING_BLOCKED",
    ]

    missing = [m for m in required_after if m not in patched_text]

    if missing:
        fail("Patch construction failed. Missing markers after patch: " + ", ".join(missing))

    return patched_text


def compile_check(path: Path) -> None:
    py_compile.compile(str(path), doraise=True)


def main() -> int:
    print("=" * 72)
    print("PATCH_003A_FILE_PATCHER_V4")
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

    ensure_no_existing_markers(text)
    print("[INFO] Existing PATCH_003A markers: absent.")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = Path(f"s43.py.PATCH_003A_V4_BACKUP_{timestamp}.bak")

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
        print("  Get-FileHash .\\s43.py -Algorithm SHA256")
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
