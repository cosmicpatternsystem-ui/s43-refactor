from pathlib import Path

p = Path("s43.py")
lines = p.read_text(encoding="utf-8").splitlines()

start = None
end = None

for i, line in enumerate(lines):
    if line.strip() == "# === PHASE54 AUDIT HELPER START ===":
        start = i
    if line.strip() == "# === PHASE54 AUDIT HELPER END ===":
        end = i
        break

if start is None or end is None or end <= start:
    raise SystemExit("ERROR: PHASE54 markers not found or invalid")

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
    "        try:",
    "            print(line)",
    "        except Exception:",
    "            pass",
    "        try:",
    "            with open(\"phase54_runtime_audit.log\", \"a\", encoding=\"utf-8\") as f:",
    "                f.write(line + \"\\n\")",
    "        except Exception:",
    "            pass",
    "    except Exception:",
    "        pass",
    "# === PHASE54 AUDIT HELPER END ===",
]

lines[start:end+1] = replacement
p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"patched PHASE54 helper block: lines {start+1}..{end+1}")
