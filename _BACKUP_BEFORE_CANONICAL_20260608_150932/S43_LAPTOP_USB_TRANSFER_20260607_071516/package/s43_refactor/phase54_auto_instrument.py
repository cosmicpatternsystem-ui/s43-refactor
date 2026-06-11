#!/usr/bin/env python3
import re
import shutil
import time
from pathlib import Path

TARGET = Path("s43.py")
TS = int(time.time())
BACKUP = Path(f"s43_before_phase54_instrument_{TS}.py")
REPORT = Path(f"phase54_instrument_report_{TS}.txt")

HELPER = r'''
# === PHASE54 AUDIT HELPER START ===
def _phase54_audit_log(event, **kw):
    try:
        import time as _t
        parts = [f"[PHASE54] {int(_t.time())} {event}"]
        for k, v in kw.items():
            try:
                parts.append(f"{k}={v!r}")
            except Exception:
                parts.append(f"{k}=<unrepr>")
        line = " | ".join(parts)
        try:
            print(line)
        except Exception:
            pass
        try:
            with open("phase54_runtime_audit.log", "a", encoding="utf-8") as f:
                f.write(line + "\\n")
        except Exception:
            pass
    except Exception:
        pass
# === PHASE54 AUDIT HELPER END ===
'''.strip("\n")

def read():
    return TARGET.read_text(encoding="utf-8", errors="replace")

def write(txt):
    TARGET.write_text(txt, encoding="utf-8")

def inject_helper(text, report):
    if "_phase54_audit_log(" in text:
        report.append("helper already exists")
        return text
    # insert after imports / near top
    lines = text.splitlines()
    insert_at = 0
    last_import = -1
    for i, line in enumerate(lines[:250]):
        s = line.strip()
        if s.startswith("import ") or s.startswith("from "):
            last_import = i
    if last_import >= 0:
        insert_at = last_import + 1
    new_lines = lines[:insert_at] + ["", HELPER, ""] + lines[insert_at:]
    report.append(f"helper inserted after line {insert_at}")
    return "\n".join(new_lines)

def instrument_function_block(text, func_name, report):
    pattern = re.compile(rf'^(\s*)(async\s+def|def)\s+{re.escape(func_name)}\s*\((.*?)\)\s*:\s*$', re.M)
    m = pattern.search(text)
    if not m:
        report.append(f"{func_name}: definition not found")
        return text

    indent = m.group(1)
    body_indent = indent + "    "
    start = m.end()

    inject = (
        f'\n{body_indent}try:\n'
        f'{body_indent}    _phase54_audit_log("{func_name}_enter")\n'
        f'{body_indent}except Exception:\n'
        f'{body_indent}    pass\n'
    )

    if f'_phase54_audit_log("{func_name}_enter")' in text[m.start():m.start()+600]:
        report.append(f"{func_name}: entry log already present")
        return text

    text = text[:start] + inject + text[start:]
    report.append(f"{func_name}: entry instrumentation added")

    # add except log for TemporaryPause if function has except TemporaryPause
    text2 = re.sub(
        rf'(^[ \t]*except[ \t]+TemporaryPause(?:[ \t]+as[ \t]+(\w+))?[ \t]*:[ \t]*$)',
        lambda mm: mm.group(1) + "\n" +
        f"{body_indent}    " + (
            f'_phase54_audit_log("{func_name}_except_TemporaryPause", exc={mm.group(2) or "None"})'
        ),
        text,
        flags=re.M
    )
    if text2 != text:
        report.append(f"{func_name}: TemporaryPause except log injected")
        text = text2

    # add except log for TradingHalt if present
    text2 = re.sub(
        rf'(^[ \t]*except[ \t]+TradingHalt(?:[ \t]+as[ \t]+(\w+))?[ \t]*:[ \t]*$)',
        lambda mm: mm.group(1) + "\n" +
        f"{body_indent}    " + (
            f'_phase54_audit_log("{func_name}_except_TradingHalt", exc={mm.group(2) or "None"})'
        ),
        text,
        flags=re.M
    )
    if text2 != text:
        report.append(f"{func_name}: TradingHalt except log injected")
        text = text2

    return text

def instrument_raise_temporary_pause(text, report):
    lines = text.splitlines()
    changed = 0
    out = []
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = line[:len(line)-len(stripped)]
        if "raise TemporaryPause(" in line and "_phase54_audit_log(" not in line:
            out.append(f'{indent}try:')
            out.append(f'{indent}    _phase54_audit_log("raise_TemporaryPause", line={i+1})')
            out.append(f'{indent}except Exception:')
            out.append(f'{indent}    pass')
            out.append(line)
            changed += 1
        else:
            out.append(line)
    report.append(f"raise TemporaryPause instrumentation count={changed}")
    return "\n".join(out)

def instrument_raise_tradinghalt(text, report):
    lines = text.splitlines()
    changed = 0
    out = []
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        indent = line[:len(line)-len(stripped)]
        if "raise TradingHalt(" in line and "_phase54_audit_log(" not in line:
            out.append(f'{indent}try:')
            out.append(f'{indent}    _phase54_audit_log("raise_TradingHalt", line={i+1})')
            out.append(f'{indent}except Exception:')
            out.append(f'{indent}    pass')
            out.append(line)
            changed += 1
        else:
            out.append(line)
    report.append(f"raise TradingHalt instrumentation count={changed}")
    return "\n".join(out)

def main():
    if not TARGET.exists():
        print("ERROR: s43.py not found")
        raise SystemExit(1)

    shutil.copy2(TARGET, BACKUP)
    report = [f"backup={BACKUP}"]

    text = read()
    original = text

    text = inject_helper(text, report)

    for fn in ["place_order", "_place", "_execute_trade"]:
        text = instrument_function_block(text, fn, report)

    text = instrument_raise_temporary_pause(text, report)
    text = instrument_raise_tradinghalt(text, report)

    if text == original:
        report.append("no changes made")
    else:
        write(text)
        report.append("instrumentation written to s43.py")

    REPORT.write_text("\n".join(report), encoding="utf-8")
    print(f"[OK] backup: {BACKUP}")
    print(f"[OK] report: {REPORT}")
    print("[OK] instrumentation patch applied")

if __name__ == "__main__":
    main()
