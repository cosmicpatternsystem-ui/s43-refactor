#!/usr/bin/env python3
from pathlib import Path
import time

TARGET = Path("s43.py")
TS = int(time.time())
OUT = Path(f"phase54_context_extract_{TS}.txt")

LINES_OF_INTEREST = [
    3219, 3224,
    3322, 3327,
    3443, 3448,
    3891,
    4133, 4138,
    4258, 4263,
    4393, 4398,
    8635, 8667,
    9338,
    11317, 11365, 11370, 11418,
    11515, 11666,
]

def main():
    text = TARGET.read_text(encoding="utf-8", errors="replace").splitlines()
    out = []
    out.append(f"target={TARGET}")
    out.append("")

    seen = set()
    for ln in LINES_OF_INTEREST:
        start = max(1, ln - 12)
        end = min(len(text), ln + 18)
        key = (start, end)
        if key in seen:
            continue
        seen.add(key)
        out.append("=" * 80)
        out.append(f"CONTEXT around line {ln} ({start}-{end})")
        out.append("=" * 80)
        for i in range(start, end + 1):
            mark = ">>>" if i == ln else "   "
            out.append(f"{mark} {i:05d}: {text[i-1]}")
        out.append("")

    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"[OK] wrote {OUT}")

if __name__ == "__main__":
    main()
