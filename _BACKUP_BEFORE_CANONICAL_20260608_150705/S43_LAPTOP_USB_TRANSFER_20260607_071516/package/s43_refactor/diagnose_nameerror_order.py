from pathlib import Path
import re

TARGET = Path("s43.py")
lines = TARGET.read_text(encoding="utf-8").splitlines()

print(f"[INFO] total lines: {len(lines)}")

print("\n[LINE 105-130]")
for n in range(105, min(130, len(lines)) + 1):
    print(f"{n}: {lines[n-1]}")

patterns = {
    "class TradingBotBase": re.compile(r"^\s*class\s+TradingBotBase\b"),
    "class TradingBotOps": re.compile(r"^\s*class\s+TradingBotOps\b"),
    "class TradingBot": re.compile(r"^\s*class\s+TradingBot\b"),
    "TradingBotBase any": re.compile(r"\bTradingBotBase\b"),
    "TradingBotOps any": re.compile(r"\bTradingBotOps\b"),
}

print("\n[CLASS DEFINITIONS]")
for name, rx in patterns.items():
    hits = []
    for i, line in enumerate(lines, 1):
        if rx.search(line):
            hits.append((i, line))
    print(f"\n{name}: {len(hits)} hit(s)")
    for i, line in hits[:30]:
        print(f"{i}: {line}")
    if len(hits) > 30:
        print(f"... truncated, total={len(hits)}")

print("\n[EARLY REFERENCES BEFORE LINE 500]")
for i, line in enumerate(lines[:500], 1):
    if "TradingBotBase" in line or "TradingBotOps" in line or "class TradingBot" in line:
        print(f"{i}: {line}")

print("\n[DONE] diagnostic only, no file modified")
