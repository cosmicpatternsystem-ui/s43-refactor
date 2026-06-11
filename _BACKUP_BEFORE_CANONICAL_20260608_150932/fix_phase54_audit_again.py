from pathlib import Path
import shutil, time

p = Path("s43.py")
bak = Path(f"s43.py.bak_fix_phase54_again_{int(time.time())}")
shutil.copy2(p, bak)

lines = p.read_text(encoding="utf-8").splitlines()

start = None
end = None

for i, line in enumerate(lines):
    if line.strip() == "# === PHASE54 AUDIT HELPER START ===":
        start = i
        break

if start is None:
    raise SystemExit("ERROR: PHASE54 START marker not found")

for j in range(start + 1, min(len(lines), start + 120)):
    if lines[j].strip() == "# === PHASE54 AUDIT HELPER END ===":
        end = j
        break

if end is None:
    raise SystemExit("ERROR: PHASE54 END marker not found")

replacement = [
    "# === PHASE54 AUDIT HELPER START ===",
    "def _phase54_audit_log(event, **kw):",
    "    try:",
    "        import time as _t",
    "        parts = [f\"[PHASE54] {int(_t.time())} {event}\"]",
    "        for k, v in kw.items():",
    "            try:",
    "                parts.append(f\"{k}={v!r}\")",
    "            except Exception:",
    "                parts.append(f\"{k}=<unrepr>\")",
    "        line = \" | \".join(parts)",
    "",
    "        try:",
    "            print(line)",
    "        except Exception:",
    "            pass",
    "",
    "        try:",
    "            with open(\"phase54_runtime_audit.log\", \"a\", encoding=\"utf-8\") as f:",
    "                f.write(line + \"\\n\")",
    "        except Exception:",
    "            pass",
    "    except Exception:",
    "        pass",
    "# === PHASE54 AUDIT HELPER END ===",
]

lines[start:end + 1] = replacement

p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"patched PHASE54 helper again: lines {start+1}..{end+1}; backup={bak}")
