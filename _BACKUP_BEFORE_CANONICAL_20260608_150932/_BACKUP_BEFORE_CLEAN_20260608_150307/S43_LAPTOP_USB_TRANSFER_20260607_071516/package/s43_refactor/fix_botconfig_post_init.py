from pathlib import Path

p = Path("s43.py")
lines = p.read_text(encoding="utf-8").splitlines()

start = None
end = None

for i, line in enumerate(lines):
    if line.strip() == "def __post_init__(self) -> None:":
        start = i
        break

if start is None:
    raise SystemExit("ERROR: __post_init__ not found")

for j in range(start + 1, min(len(lines), start + 120)):
    if lines[j].startswith("class _DashRingHandler"):
        end = j
        break

if end is None:
    raise SystemExit("ERROR: class _DashRingHandler boundary not found")

replacement = [
    "    def __post_init__(self) -> None:",
    "        'Normalize symbol lists so the rest of the bot always sees proper market pairs.'",
    "        try:",
    "            dq = str(getattr(self, \"quote\", \"IRT\") or \"IRT\").upper()",
    "        except Exception:",
    "            dq = \"IRT\"",
    "",
    "        def _norm_list(lst):",
    "            out = []",
    "            seen = set()",
    "            for s in (lst or []):",
    "                try:",
    "                    cs = _canon_pair(s, dq)",
    "                except Exception:",
    "                    cs = str(s or \"\").strip().upper()",
    "                if not cs:",
    "                    continue",
    "                if cs == dq:",
    "                    continue",
    "                if cs not in seen:",
    "                    seen.add(cs)",
    "                    out.append(cs)",
    "            return out",
    "",
    "        try:",
    "            object.__setattr__(self, \"symbols\", _norm_list(getattr(self, \"symbols\", None)))",
    "        except Exception:",
    "            pass",
    "        try:",
    "            object.__setattr__(self, \"symbol_priority\", _norm_list(getattr(self, \"symbol_priority\", None)))",
    "        except Exception:",
    "            pass",
    "        try:",
    "            object.__setattr__(self, \"flash_ref_symbols\", _norm_list(getattr(self, \"flash_ref_symbols\", None)))",
    "        except Exception:",
    "            pass",
    "",
]

lines[start:end] = replacement

p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"patched BotConfig.__post_init__: lines {start+1}..{end}")
