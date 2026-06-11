from pathlib import Path
import shutil, time

p = Path("s43.py")
bak = Path(f"s43.py.bak_fix_parse_age_{int(time.time())}")
shutil.copy2(p, bak)

lines = p.read_text(encoding="utf-8").splitlines()

start = None
end = None

for i, line in enumerate(lines):
    if line.strip().startswith("def _parse_age("):
        start = i
        break

if start is None:
    raise SystemExit("ERROR: def _parse_age not found")

for j in range(start + 1, min(len(lines), start + 120)):
    if lines[j].strip().startswith("class ExecutionEngine"):
        end = j
        break

if end is None:
    raise SystemExit("ERROR: class ExecutionEngine boundary not found")

replacement = [
    "def _parse_age(tag: str) -> Optional[float]:",
    "    try:",
    "        if tag is None:",
    "            return None",
    "        s = str(tag).strip().lower()",
    "        if not s:",
    "            return None",
    "",
    "        m = re.search(r'([0-9]+(?:\\.[0-9]+)?)\\s*([smhd])', s)",
    "        if not m:",
    "            return None",
    "",
    "        v = float(m.group(1))",
    "        u = m.group(2)",
    "        if u == 's':",
    "            return v",
    "        if u == 'm':",
    "            return v * 60.0",
    "        if u == 'h':",
    "            return v * 3600.0",
    "        if u == 'd':",
    "            return v * 86400.0",
    "        return None",
    "    except Exception:",
    "        return None",
    "",
]

lines[start:end] = replacement

p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"patched _parse_age: lines {start+1}..{end}; backup={bak}")
