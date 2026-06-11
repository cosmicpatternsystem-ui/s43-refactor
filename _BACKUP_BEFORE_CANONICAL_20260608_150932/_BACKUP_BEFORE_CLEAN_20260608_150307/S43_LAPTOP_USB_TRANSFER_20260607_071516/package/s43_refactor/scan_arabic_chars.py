import pathlib
import sys

found = False
for path in pathlib.Path(".").glob("*.py"):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_no, line in enumerate(text.splitlines(), 1):
            if any(0x0600 <= ord(ch) <= 0x06FF for ch in line):
                found = True
                print(f"ARABIC_FOUND: {path} L{line_no}")
    except: pass

if not found: print("OK: No Arabic chars")
sys.exit(1 if found else 0)
